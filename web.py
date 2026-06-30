import os
from datetime import datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for

from baby_milk_tracker.auth import get_user_by_credentials
from baby_milk_tracker.database import init_db
from baby_milk_tracker.migrations import run_migrations
from baby_milk_tracker.models import BabyProfile, Feeding, GrowthRecord, Pumping
from baby_milk_tracker.percentiles import (
    get_length_percentile,
    get_weight_percentile,
    is_percentile_supported,
)
from baby_milk_tracker.storage import (
    delete_all_records,
    delete_feeding,
    delete_growth_record,
    delete_pumping,
    get_all_feedings,
    get_all_pumpings,
    get_baby_for_user,
    get_feedings_since,
    get_growth_records,
    get_last_feeding,
    get_last_growth_record,
    get_last_pumping,
    get_pumpings_since,
    get_start_datetime,
    save_baby,
    save_feeding,
    save_growth_record,
    save_pumping,
)
from baby_milk_tracker.time_utils import (
    ARGENTINA_TIMEZONE,
    from_baby_age,
    now_argentina,
)

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "baby-milk-tracker-local-secret")

init_db()
run_migrations()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return view(**kwargs)

    return wrapped_view


def get_created_at_from_form():
    created_at = request.form.get("created_at")

    if not created_at:
        return now_argentina()

    return datetime.fromisoformat(created_at).replace(tzinfo=ARGENTINA_TIMEZONE)


def current_baby_id() -> int | None:
    return session.get("baby_id")


@app.route("/")
@login_required
def index():
    baby_id = current_baby_id()
    baby_profile = get_baby_for_user(session["user_id"])

    last_feeding = get_last_feeding(baby_id) if baby_id else None
    last_pumping = get_last_pumping(baby_id) if baby_id else None
    last_growth_record = get_last_growth_record(baby_id) if baby_id else None

    baby_age_days = None
    formatted_baby_age = None

    last_growth_age_days = None
    formatted_last_growth_age = None

    if baby_profile:
        baby_age_days = (now_argentina().date() - baby_profile.birth_date.date()).days
        formatted_baby_age = from_baby_age(baby_age_days)

    weight_percentile = None
    length_percentile = None
    percentile_status = None

    if baby_profile and last_growth_record and baby_age_days is not None:
        weight_percentile = get_weight_percentile(
            baby_profile,
            last_growth_record,
        )

        length_percentile = get_length_percentile(
            baby_profile,
            last_growth_record,
        )

        last_growth_age_days = (
            last_growth_record.created_at.date() - baby_profile.birth_date.date()
        ).days

        formatted_last_growth_age = from_baby_age(last_growth_age_days)

        if is_percentile_supported(baby_profile, last_growth_record):
            percentile_status = "available"
        elif baby_profile.sex != "female":
            percentile_status = "female_only"
        elif last_growth_age_days < 0:
            percentile_status = "before_birth"
        else:
            percentile_status = "age_out_of_range"

    return render_template(
        "index.html",
        last_feeding=last_feeding,
        last_pumping=last_pumping,
        baby_profile=baby_profile,
        last_growth_record=last_growth_record,
        baby_age_days=baby_age_days,
        formatted_baby_age=formatted_baby_age,
        weight_percentile=weight_percentile,
        length_percentile=length_percentile,
        percentile_status=percentile_status,
        last_growth_age_days=last_growth_age_days,
        formatted_last_growth_age=formatted_last_growth_age,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        user_id = get_user_by_credentials(username, password)

        if user_id is not None:
            session["user_id"] = user_id
            session["username"] = username

            baby = get_baby_for_user(user_id)
            if baby:
                session["baby_id"] = baby.id

            return redirect(url_for("index"))

        error = "Usuario o contraseña incorrecta."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/history")
@login_required
def history():
    baby_id = current_baby_id()
    range_name = request.args.get("range", "week")

    if baby_id is None:
        feedings, pumpings = [], []
    elif range_name == "all":
        feedings = get_all_feedings(baby_id)
        pumpings = get_all_pumpings(baby_id)
    else:
        start_datetime = get_start_datetime(range_name)
        feedings = get_feedings_since(start_datetime, baby_id)
        pumpings = get_pumpings_since(start_datetime, baby_id)

    return render_template(
        "history.html",
        feedings=feedings,
        pumpings=pumpings,
        selected_range=range_name,
    )


@app.route("/feeding/<int:feeding_id>/delete", methods=["POST"])
@login_required
def delete_feeding_route(feeding_id: int):
    range_name = request.args.get("range", "week")
    delete_feeding(feeding_id)
    return redirect(f"/history?range={range_name}")


@app.route("/pumping/<int:pumping_id>/delete", methods=["POST"])
@login_required
def delete_pumping_route(pumping_id: int):
    range_name = request.args.get("range", "week")
    delete_pumping(pumping_id)
    return redirect(f"/history?range={range_name}")


@app.route("/pumping/new", methods=["GET", "POST"])
@login_required
def new_pumping():
    if request.method == "POST":
        baby_id = current_baby_id()
        pumping = Pumping(
            created_at=get_created_at_from_form(),
            amount_ml=int(request.form["amount_ml"]),
            side=request.form["side"],
        )
        save_pumping(pumping, baby_id)
        return redirect("/")

    return render_template("pumping_form.html")


@app.route("/feeding/new", methods=["GET", "POST"])
@login_required
def new_feeding():
    if request.method == "POST":
        baby_id = current_baby_id()
        feeding_type = request.form["feeding_type"]

        duration_min = request.form.get("duration_min")
        duration_min = int(duration_min) if duration_min else None

        if feeding_type == "breast":
            feeding = Feeding(
                created_at=get_created_at_from_form(),
                feeding_type="breast",
                side=request.form["side"],
                duration_min=duration_min,
                amount_ml=None,
            )
        else:
            amount_ml = request.form.get("amount_ml")
            feeding = Feeding(
                created_at=get_created_at_from_form(),
                feeding_type="bottle",
                side=None,
                duration_min=duration_min,
                amount_ml=int(amount_ml),
            )

        save_feeding(feeding, baby_id)
        return redirect("/")

    return render_template("feeding_form.html")


@app.route("/records/delete-all", methods=["POST"])
@login_required
def delete_records():
    baby_id = current_baby_id()
    if baby_id:
        delete_all_records(baby_id)
    return redirect("/")


@app.route("/charts")
@login_required
def charts():
    baby_id = current_baby_id()
    range_name = request.args.get("range", "day")
    start_datetime = get_start_datetime(range_name)

    pumpings = get_pumpings_since(start_datetime, baby_id) if baby_id else []
    feedings = get_feedings_since(start_datetime, baby_id) if baby_id else []

    pumping_chart_data = [
        {
            "time": pumping.created_at.strftime("%d/%m %H:%M"),
            "amount_ml": pumping.amount_ml,
            "side": pumping.side,
        }
        for pumping in pumpings
    ]

    feeding_chart_data = []
    for feeding in feedings:
        label = feeding.side if feeding.feeding_type == "breast" else "bottle"
        feeding_chart_data.append(
            {
                "time": feeding.created_at.strftime("%d/%m %H:%M"),
                "type": feeding.feeding_type,
                "label": label,
                "amount_ml": feeding.amount_ml,
                "duration_min": feeding.duration_min,
            }
        )

    return render_template(
        "charts.html",
        range_name=range_name,
        pumping_chart_data=pumping_chart_data,
        feeding_chart_data=feeding_chart_data,
    )


@app.route("/growth")
@login_required
def growth():
    baby_id = current_baby_id()
    records = get_growth_records(baby_id) if baby_id else []
    baby_profile = get_baby_for_user(session["user_id"])

    if baby_profile:
        for record in records:
            growth_record = GrowthRecord(
                created_at=record["created_at"],
                weight_kg=record["weight_kg"],
                length_cm=record["length_cm"],
                head_circumference_cm=record["head_circumference_cm"],
            )
            record["weight_percentile"] = get_weight_percentile(
                baby_profile, growth_record
            )
            record["length_percentile"] = get_length_percentile(
                baby_profile, growth_record
            )
            age_days = (
                growth_record.created_at.date() - baby_profile.birth_date.date()
            ).days
            record["formatted_age"] = from_baby_age(age_days) if age_days >= 0 else None

    return render_template(
        "growth.html",
        records=records,
        baby_profile=baby_profile,
    )


@app.route("/growth/new", methods=["GET", "POST"])
@login_required
def new_growth():
    if request.method == "POST":
        baby_id = current_baby_id()
        head_circumference_cm = request.form.get("head_circumference_cm")
        created_at_raw = request.form.get("created_at")

        created_at = (
            datetime.fromisoformat(created_at_raw)
            if created_at_raw
            else now_argentina()
        )

        growth_record = GrowthRecord(
            created_at=created_at,
            weight_kg=float(request.form["weight_kg"]),
            length_cm=float(request.form["length_cm"]),
            head_circumference_cm=(
                float(head_circumference_cm) if head_circumference_cm else None
            ),
        )
        save_growth_record(growth_record, baby_id)
        return redirect(url_for("growth"))

    return render_template("growth_form.html")


@app.route("/growth/<int:growth_record_id>/delete", methods=["POST"])
@login_required
def delete_growth_record_route(growth_record_id: int):
    delete_growth_record(growth_record_id)
    return redirect(url_for("growth"))


@app.route("/baby-profile", methods=["GET", "POST"])
@login_required
def baby_profile():
    user_id = session["user_id"]
    profile = get_baby_for_user(user_id)

    if request.method == "POST":
        profile = BabyProfile(
            first_name=request.form["first_name"],
            last_name=request.form["last_name"],
            birth_date=datetime.fromisoformat(request.form["birth_date"]),
            sex=request.form["sex"],
        )

        baby_id = save_baby(profile, user_id)
        session["baby_id"] = baby_id

        return redirect(url_for("index"))

    return render_template(
        "baby_profile.html",
        profile=profile,
    )


if __name__ == "__main__":
    init_db()
    run_migrations()
    app.run(host="0.0.0.0", port=5000, debug=True)
