from core.objects import MagneticObject


def convert_magnetic_objects_to_magpy(magnetic_objects: list[MagneticObject]) -> list:
    magpy_objects = []

    for obj in magnetic_objects:
        try:
            magpy_obj = obj.to_magpy()
            if magpy_obj is not None:
                # Просто добавляем объект как есть, не извлекая из коллекций
                magpy_objects.append(magpy_obj)
        except Exception as e:
            print(f"Ошибка при создании magpylib объекта: {e}")
            continue

    return magpy_objects
