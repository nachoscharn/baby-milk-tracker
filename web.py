from baby_milk_tracker.time_utils import now_argentina

from flask import Flask, render_template, request, redirect

from baby_milk_tracker.database import init_db
from baby_milk_tracker.models import Feeding, Pumping
from baby_milk_tracker.storage import (
    get_last_feeding,
    get_last_pumping,
    save_feeding,
    save_pumping,
    delete_all_records,
    get_feedings_since,
    get_pumpings_since,
    get_start_datetime,

)

app = Flask(__name__)
init_db()

@app.route("/")
def index():
    last_feeding = get_last_feeding()
    last_pumping = get_last_pumping()

    return render_template(
        "index.html",
        last_feeding=last_feeding,
        last_pumping=last_pumping,
    )

@app.route("/pumping/new", methods=["GET", "POST"])
def new_pumping():
    if request.method == "POST":
        amount_ml = int(request.form["amount_ml"])
        side = request.form["side"]

        pumping = Pumping(
            created_at=now_argentina(),
            amount_ml=amount_ml,
            side=side,
        )

        save_pumping(pumping)

        return redirect("/")

    return render_template("pumping_form.html")

@app.route("/feeding/new", methods=["GET", "POST"])
def new_feeding():
    if request.method == "POST":
        feeding_type = request.form["feeding_type"]

        duration_min = request.form.get("duration_min")
        duration_min = int(duration_min) if duration_min else None

        if feeding_type == "breast":
            feeding = Feeding(
                created_at=now_argentina(),
                feeding_type="breast",
                side=request.form["side"],
                duration_min=duration_min,
                amount_ml=None,
            )

        else:
            amount_ml = request.form.get("amount_ml")

            feeding = Feeding(
                created_at=now_argentina(),
                feeding_type="bottle",
                side=None,
                duration_min=duration_min,
                amount_ml=int(amount_ml),
            )

        save_feeding(feeding)

        return redirect("/")

    return render_template("feeding_form.html")

@app.route("/records/delete-all", methods=["POST"])
def delete_records():
    delete_all_records()
    return redirect("/")
@app.route("/charts")
def charts():
    range_name = request.args.get("range", "day")

    start_datetime = get_start_datetime(range_name)

    pumpings = get_pumpings_since(start_datetime)
    feedings = get_feedings_since(start_datetime)

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
        if feeding.feeding_type == "breast":
            label = feeding.side
        else:
            label = "bottle"

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

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

