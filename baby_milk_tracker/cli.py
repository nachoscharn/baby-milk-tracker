from datetime import datetime

from baby_milk_tracker.models import Feeding, Pumping
from baby_milk_tracker.storage import save_feeding, save_pumping
from baby_milk_tracker.time_utils import now_argentina


def run_menu():
    print("Baby Milk Tracker")
    print("Bienvenido")

    while True:
        print("\nPor favor elija una opción:")
        print("1) Registrar toma")
        print("2) Registrar extracción")
        print("3) Salir")

        option = input("Opción: ")

        if option == "1":
            feeding = register_feeding()
            print_feeding(feeding)

            if confirm_save():
                save_feeding(feeding)
                print("Registro guardado correctamente")
            else:
                print("Registro descartado")

        elif option == "2":
            pumping = register_pumping()
            print_pumping(pumping)

            if confirm_save():
                save_pumping(pumping)
                print("Registro guardado correctamente")
            else:
                print("Registro descartado")

        elif option == "3":
            print("Saliendo")
            break

        else:
            print(f"Su opción ({option}) es inválida, por favor elija nuevamente")


def confirm_save() -> bool:
    while True:
        option = input("\n¿Está bien la información cargada? ¿Desea guardar? (s/n): ")

        if option.lower() == "s":
            return True

        if option.lower() == "n":
            return False

        print(f"Opción inválida: {option}")


def register_feeding() -> Feeding:
    created_at = now_argentina()

    while True:
        feeding_type = input(
            "\n¿Cómo se alimentó?\n" "1) Pecho\n" "2) Mamadera\n" "Opción: "
        )

        if feeding_type in ["1", "2"]:
            break

        print(f"Tipo de alimentación inválido: {feeding_type}")

    if feeding_type == "1":
        return register_breast_feeding(created_at)

    return register_bottle_feeding(created_at)


def register_breast_feeding(created_at: datetime) -> Feeding:
    while True:
        side = input(
            "\n¿Qué pecho se usó?\n" "1) Izquierdo\n" "2) Derecho\n" "Opción: "
        )

        if side == "1":
            side_name = "left"
            break

        if side == "2":
            side_name = "right"
            break

        print(f"Lado inválido: {side}")

    duration_min = int(input("¿Cuántos minutos tomó?: "))

    return Feeding(
        created_at=created_at,
        feeding_type="breast",
        side=side_name,
        duration_min=duration_min,
    )


def register_bottle_feeding(created_at: datetime) -> Feeding:
    amount_ml = int(input("¿Cuántos ml tomó?: "))

    return Feeding(
        created_at=created_at,
        feeding_type="bottle",
        amount_ml=amount_ml,
    )


def print_feeding(feeding: Feeding) -> None:
    print("\nToma registrada correctamente")
    print(f"Hora: {feeding.created_at.strftime('%d/%m/%Y %H:%M')}")

    if feeding.feeding_type == "breast":
        side = "izquierdo" if feeding.side == "left" else "derecho"
        print("Tipo: Pecho")
        print(f"Lado: {side}")
        print(f"Duración: {feeding.duration_min} min")

    elif feeding.feeding_type == "bottle":
        print("Tipo: Mamadera")
        print(f"Cantidad: {feeding.amount_ml} ml")


def register_pumping() -> Pumping:
    created_at = now_argentina()

    amount_ml = int(input("¿Cuántos ml se extrajo?: "))

    while True:
        side = input(
            "\n¿De qué lado fue la extracción?\n"
            "1) Izquierdo\n"
            "2) Derecho\n"
            "3) Ambos\n"
            "Opción: "
        )

        if side == "1":
            side_name = "left"
            break

        if side == "2":
            side_name = "right"
            break

        if side == "3":
            side_name = "both"
            break

        print(f"Lado inválido: {side}")

    return Pumping(
        created_at=created_at,
        amount_ml=amount_ml,
        side=side_name,
    )


def print_pumping(pumping: Pumping) -> None:
    side_map = {
        "left": "izquierdo",
        "right": "derecho",
        "both": "ambos",
    }

    print("\nExtracción registrada correctamente")
    print(f"Hora: {pumping.created_at.strftime('%d/%m/%Y %H:%M')}")
    print(f"Cantidad: {pumping.amount_ml} ml")
    print(f"Lado: {side_map[pumping.side]}")
