import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for

from baby_milk_tracker.auth import get_user_by_credentials
from baby_milk_tracker.database import init_db
from baby_milk_tracker.migrations import run_migrations
from baby_milk_tracker.models import (
    Appointment,
    BabyProfile,
    Feeding,
    GrowthRecord,
    MedicalStudy,
    Medication,
    Pumping,
)
from baby_milk_tracker.percentiles import (
    MAX_AGE_DAYS,
    PERCENTILES,
    get_length_percentile,
    get_length_percentile_curves,
    get_weight_percentile,
    get_weight_percentile_curves,
    is_percentile_supported,
)
from baby_milk_tracker.storage import (
    delete_appointment,
    delete_feeding,
    delete_growth_record,
    delete_medical_study,
    delete_medication,
    delete_pumping,
    finish_feeding,
    get_active_medications,
    get_all_feedings,
    get_all_medications,
    get_all_pumpings,
    get_appointments,
    get_baby_for_user,
    get_feedings_since,
    get_growth_records,
    get_last_feeding,
    get_last_growth_record,
    get_last_length_record,
    get_last_pumping,
    get_last_weight_record,
    get_medical_studies,
    get_medication,
    get_next_appointment,
    get_pumpings_since,
    get_start_datetime,
    get_user_settings,
    record_medication_dose,
    save_appointment,
    save_baby,
    save_feeding,
    save_growth_record,
    save_medical_study,
    save_medication,
    save_pumping,
    save_user_settings,
)
from baby_milk_tracker.time_utils import (
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
        return now_argentina().replace(tzinfo=None)

    return datetime.fromisoformat(created_at)


def current_baby_id() -> int | None:
    return session.get("baby_id")


@app.route("/")
@login_required
def index():
    baby_id = current_baby_id()
    baby_profile = get_baby_for_user(session["user_id"])

    settings = get_user_settings(session["user_id"])

    last_feeding = get_last_feeding(baby_id) if baby_id else None
    last_pumping = (
        get_last_pumping(baby_id) if baby_id and settings["show_pumpings"] else None
    )
    last_growth_record = get_last_growth_record(baby_id) if baby_id else None
    last_weight_record = get_last_weight_record(baby_id) if baby_id else None
    last_length_record = get_last_length_record(baby_id) if baby_id else None
    next_appointment = get_next_appointment(baby_id) if baby_id else None

    today_ml = 0
    recommended_ml = None
    if baby_id:
        today_start = now_argentina().replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        )
        today_feedings = get_feedings_since(today_start, baby_id)
        today_ml = sum(f.amount_ml for f in today_feedings if f.amount_ml)
        if settings.get("daily_ml_target"):
            recommended_ml = settings["daily_ml_target"]
        elif last_weight_record:
            recommended_ml = int(last_weight_record.weight_kg * 200)

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
        weight_percentile = (
            get_weight_percentile(baby_profile, last_weight_record)
            if last_weight_record
            else None
        )

        length_percentile = (
            get_length_percentile(baby_profile, last_length_record)
            if last_length_record
            else None
        )

        last_growth_age_days = (
            last_growth_record.created_at.date() - baby_profile.birth_date.date()
        ).days

        formatted_last_growth_age = from_baby_age(last_growth_age_days)

        if is_percentile_supported(baby_profile, last_growth_record):
            percentile_status = "available"
        elif last_growth_age_days < 0:
            percentile_status = "before_birth"
        else:
            percentile_status = "age_out_of_range"

    now_arg = now_argentina().replace(tzinfo=None)
    active_medications = (
        [
            _medication_display(m, now_arg)
            for m in get_active_medications(baby_id, session["user_id"])
        ]
        if baby_id
        else []
    )

    return render_template(
        "index.html",
        last_feeding=last_feeding,
        last_pumping=last_pumping,
        baby_profile=baby_profile,
        active_medications=active_medications,
        last_growth_record=last_growth_record,
        baby_age_days=baby_age_days,
        formatted_baby_age=formatted_baby_age,
        weight_percentile=weight_percentile,
        length_percentile=length_percentile,
        percentile_status=percentile_status,
        last_growth_age_days=last_growth_age_days,
        formatted_last_growth_age=formatted_last_growth_age,
        next_appointment=next_appointment,
        settings=settings,
        today_ml=today_ml,
        recommended_ml=recommended_ml,
        baby_id=baby_id,
    )


@app.route("/ping")
def ping():
    return "ok", 200


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
    user_settings = get_user_settings(session["user_id"])

    if baby_id is None:
        feedings, pumpings = [], []
    elif range_name == "all":
        feedings = get_all_feedings(baby_id)
        pumpings = get_all_pumpings(baby_id) if user_settings["show_pumpings"] else []
    else:
        start_datetime = get_start_datetime(range_name)
        feedings = get_feedings_since(start_datetime, baby_id)
        pumpings = (
            get_pumpings_since(start_datetime, baby_id)
            if user_settings["show_pumpings"]
            else []
        )

    return render_template(
        "history.html",
        feedings=feedings,
        pumpings=pumpings,
        selected_range=range_name,
        settings=user_settings,
    )


@app.route("/feeding/<int:feeding_id>/finish", methods=["POST"])
@login_required
def finish_feeding_route(feeding_id: int):
    last = get_last_feeding(current_baby_id())
    if last and last.id == feeding_id and last.duration_min is None:
        elapsed = now_argentina().replace(tzinfo=None) - last.created_at
        duration_min = max(1, int(elapsed.total_seconds() / 60))
        finish_feeding(feeding_id, duration_min)
    return redirect(url_for("index"))


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
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    if request.method == "POST":
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
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    if request.method == "POST":
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

    settings = get_user_settings(session["user_id"])
    return render_template("feeding_form.html", settings=settings)


@app.route("/growth")
@login_required
def growth():
    return redirect(url_for("growth_chart"))


@app.route("/growth/history")
@login_required
def growth_history():
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
            record["weight_percentile"] = (
                get_weight_percentile(baby_profile, growth_record)
                if growth_record.weight_kg is not None
                else None
            )
            record["length_percentile"] = (
                get_length_percentile(baby_profile, growth_record)
                if growth_record.length_cm is not None
                else None
            )
            age_days = (
                growth_record.created_at.date() - baby_profile.birth_date.date()
            ).days
            record["formatted_age"] = from_baby_age(age_days) if age_days >= 0 else None

    return render_template(
        "growth_history.html",
        records=records,
        baby_profile=baby_profile,
    )


@app.route("/growth/new", methods=["GET", "POST"])
@login_required
def new_growth():
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    if request.method == "POST":
        head_circumference_cm = request.form.get("head_circumference_cm")
        created_at_raw = request.form.get("created_at")

        created_at = (
            datetime.fromisoformat(created_at_raw)
            if created_at_raw
            else now_argentina().replace(tzinfo=None)
        )

        weight_kg_raw = request.form.get("weight_kg")
        length_cm_raw = request.form.get("length_cm")

        growth_record = GrowthRecord(
            created_at=created_at,
            weight_kg=float(weight_kg_raw) if weight_kg_raw else None,
            length_cm=float(length_cm_raw) if length_cm_raw else None,
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
    return redirect(url_for("growth_history"))


@app.route("/growth/chart")
@login_required
def growth_chart():
    baby_id = current_baby_id()
    baby_profile = get_baby_for_user(session["user_id"])

    if not baby_profile or not baby_id:
        return redirect(url_for("growth"))

    records = get_growth_records(baby_id)

    current_age_days = (now_argentina().date() - baby_profile.birth_date.date()).days
    max_chart_weeks = min(int(current_age_days / 7), int(MAX_AGE_DAYS / 7))

    baby_weight_data = []
    baby_length_data = []
    for record in records:
        age_days = (record["created_at"].date() - baby_profile.birth_date.date()).days
        if age_days >= 0:
            age_weeks = round(age_days / 7, 1)
            if record["weight_kg"] is not None:
                baby_weight_data.append({"x": age_weeks, "y": record["weight_kg"]})
            if record["length_cm"] is not None:
                baby_length_data.append({"x": age_weeks, "y": record["length_cm"]})

    baby_weight_data.sort(key=lambda p: p["x"])
    baby_length_data.sort(key=lambda p: p["x"])

    weight_curves = get_weight_percentile_curves(baby_profile.sex, max_chart_weeks)
    length_curves = get_length_percentile_curves(baby_profile.sex, max_chart_weeks)

    return render_template(
        "growth_chart.html",
        baby_profile=baby_profile,
        baby_weight_data=baby_weight_data,
        baby_length_data=baby_length_data,
        weight_curves=weight_curves,
        length_curves=length_curves,
        percentiles=PERCENTILES,
    )


@app.route("/appointments")
@login_required
def appointments():
    baby_id = current_baby_id()
    items = get_appointments(baby_id) if baby_id else []
    now = now_argentina().replace(tzinfo=None)
    return render_template("appointments.html", appointments=items, now=now)


@app.route("/appointments/new", methods=["GET", "POST"])
@login_required
def new_appointment():
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    if request.method == "POST":
        appointment = Appointment(
            appointment_datetime=datetime.fromisoformat(
                request.form["appointment_datetime"]
            ),
            doctor_specialty=request.form["doctor_specialty"],
            location=request.form.get("location") or None,
        )
        save_appointment(appointment, baby_id)
        return redirect(url_for("appointments"))
    return render_template("appointment_form.html")


@app.route("/appointments/<int:appointment_id>/delete", methods=["POST"])
@login_required
def delete_appointment_route(appointment_id: int):
    delete_appointment(appointment_id)
    return redirect(url_for("appointments"))


@app.route("/medical")
@login_required
def medical():
    baby_id = current_baby_id()
    items = get_medical_studies(baby_id) if baby_id else []
    return render_template("medical.html", studies=items)


@app.route("/medical/new", methods=["GET", "POST"])
@login_required
def new_medical_study():
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    if request.method == "POST":
        study = MedicalStudy(
            study_date=datetime.fromisoformat(request.form["study_date"]),
            study_type=request.form["study_type"],
            result=request.form.get("result") or None,
            doctor=request.form.get("doctor") or None,
        )
        save_medical_study(study, baby_id)
        return redirect(url_for("medical"))
    return render_template("medical_form.html")


@app.route("/medical/<int:study_id>/delete", methods=["POST"])
@login_required
def delete_medical_study_route(study_id: int):
    delete_medical_study(study_id)
    return redirect(url_for("medical"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session["user_id"]
    if request.method == "POST":
        save_user_settings(
            user_id,
            {"show_pumpings": "show_pumpings" in request.form},
        )
        return redirect(url_for("settings"))
    current = get_user_settings(user_id)
    return render_template("settings.html", settings=current)


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


def _medication_display(med: Medication, now: datetime) -> dict:
    last_dose = med.last_dose_at or med.start_datetime
    next_dose = last_dose + timedelta(hours=med.frequency_hours)
    minutes_until = (next_dose - now).total_seconds() / 60

    freq_h = med.frequency_hours
    if freq_h == int(freq_h):
        frequency_str = f"{int(freq_h)}h"
    else:
        h = int(freq_h)
        m = int((freq_h - h) * 60)
        frequency_str = f"{h}h {m}m" if h else f"{m}m"

    if minutes_until <= 0:
        abs_m = int(abs(minutes_until))
        h, m = divmod(abs_m, 60)
        time_str = f"hace {h}h {m}m" if h else f"hace {abs_m} min"
        status = "overdue"
    elif minutes_until < 30:
        time_str = f"en {int(minutes_until)} min"
        status = "soon"
    else:
        h = int(minutes_until // 60)
        m = int(minutes_until % 60)
        time_str = f"en {h}h {m}m" if h and m else (f"en {h}h" if h else f"en {m} min")
        status = "ok"

    return {
        "id": med.id,
        "name": med.name,
        "dose_amount": med.dose_amount,
        "next_dose_iso": next_dose.isoformat(),
        "time_str": time_str,
        "status": status,
        "frequency_str": frequency_str,
        "end_date": med.end_datetime.strftime("%d/%m/%Y"),
        "frequency_hours": med.frequency_hours,
    }


# ---------------------------------------------------------------------------
# Medications
# ---------------------------------------------------------------------------


@app.route("/medications")
@login_required
def medications():
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    user_id = session["user_id"]
    now = now_argentina().replace(tzinfo=None)
    all_meds = get_all_medications(baby_id, user_id)

    active, finished = [], []
    for med in all_meds:
        display = _medication_display(med, now)
        if med.end_datetime > now:
            active.append(display)
        else:
            finished.append(display)

    return render_template("medications.html", active=active, finished=finished)


@app.route("/medications/new", methods=["GET", "POST"])
@login_required
def new_medication():
    baby_id = current_baby_id()
    if not baby_id:
        return redirect(url_for("baby_profile"))

    if request.method == "POST":
        name = request.form["name"].strip()
        dose_amount = request.form.get("dose_amount", "").strip() or None
        frequency_hours = float(request.form["frequency_hours"])
        start_str = request.form.get("start_datetime")
        end_str = request.form.get("end_datetime")
        now_arg = now_argentina().replace(tzinfo=None)
        start_dt = datetime.fromisoformat(start_str) if start_str else now_arg
        end_dt = (
            datetime.fromisoformat(end_str) if end_str else now_arg + timedelta(days=7)
        )

        med = Medication(
            name=name,
            dose_amount=dose_amount,
            frequency_hours=frequency_hours,
            start_datetime=start_dt,
            end_datetime=end_dt,
        )
        save_medication(med, baby_id, session["user_id"])
        return redirect(url_for("medications"))

    now_str = now_argentina().replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M")
    return render_template("medication_form.html", now_str=now_str)


@app.route("/medications/<int:medication_id>/dose", methods=["GET", "POST"])
@login_required
def give_medication_dose(medication_id: int):
    user_id = session["user_id"]
    med = get_medication(medication_id, user_id)
    if not med:
        return redirect(url_for("medications"))

    if request.method == "POST":
        given_str = request.form.get("given_at")
        given_at = (
            datetime.fromisoformat(given_str)
            if given_str
            else now_argentina().replace(tzinfo=None)
        )
        record_medication_dose(medication_id, user_id, given_at)
        return redirect(url_for("index"))

    now_str = now_argentina().replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M")
    return render_template("medication_dose_form.html", med=med, now_str=now_str)


@app.route("/medications/<int:medication_id>/delete", methods=["POST"])
@login_required
def delete_medication_route(medication_id: int):
    delete_medication(medication_id, session["user_id"])
    return redirect(url_for("medications"))


if __name__ == "__main__":
    init_db()
    run_migrations()
    app.run(host="0.0.0.0", port=5000, debug=True)
