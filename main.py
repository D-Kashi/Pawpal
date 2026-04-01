from datetime import datetime
from pawpal_system import Owner, Pet, Task

# /c:/Users/dusha/Pawpal/main.py
# No additional import handling required; imports above are sufficient.

def create_task_flexible(title, time_str, **kwargs):
    # Try common Task constructors
    for ctor_args in (
        (title, time_str),
        (title, datetime.strptime(time_str, "%H:%M").time()),
        (title,),
    ):
        try:
            return Task(*ctor_args, **kwargs)
        except Exception:
            continue
    # Last resort: try keyword names
    try:
        return Task(name=title, time=time_str, **kwargs)
    except Exception as e:
        raise

def add_task_to_pet(pet, task):
    if hasattr(pet, "add_task"):
        pet.add_task(task)
    elif hasattr(pet, "tasks") and isinstance(pet.tasks, list):
        pet.tasks.append(task)
    else:
        # try common attribute names
        if hasattr(pet, "tasks_list") and isinstance(pet.tasks_list, list):
            pet.tasks_list.append(task)
        else:
            # attach a tasks list dynamically
            setattr(pet, "tasks", [task])

def get_pet_tasks(pet):
    for attr in ("tasks", "tasks_list", "schedule"):
        if hasattr(pet, attr):
            val = getattr(pet, attr)
            if isinstance(val, list):
                return val
    return []

def task_time_key(task):
    for attr in ("time", "when", "time_str"):
        if hasattr(task, attr):
            val = getattr(task, attr)
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%H:%M").time()
                except Exception:
                    pass
            if isinstance(val, datetime):
                return val.time()
            return val
    # fallback: try parsing str(task)
    s = str(task)
    try:
        return datetime.strptime(s, "%H:%M").time()
    except Exception:
        return datetime.max.time()

def task_title(task):
    for attr in ("name", "title", "description"):
        if hasattr(task, attr):
            return getattr(task, attr)
    return str(task)

def pet_name(pet):
    for attr in ("name", "nickname"):
        if hasattr(pet, attr):
            return getattr(pet, attr)
    return "Unnamed Pet"

if __name__ == "__main__":
    owner = Owner("Dusha")

    # create pets and attach
    pet1 = Pet("Fido", type="Dog", gender="male") if "type" in Pet.__init__.__code__.co_varnames else Pet("Fido")
    pet2 = Pet("Mittens", type="Cat", gender="female") if "type" in Pet.__init__.__code__.co_varnames else Pet("Mittens")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    # Create Task objects (out of chronological order) — Task.type used as label/title
    t1 = Task(type="Morning Walk", time="08:00", pet=pet1)
    t2 = Task(type="Afternoon Meal", time="12:30", pet=pet1)
    t3 = Task(type="Evening Play", time="18:15", pet=pet2)
    t4 = Task(type="Midnight Check", time="00:30", pet=pet2)

    # Add tasks to schedule out of order
    owner.add_task(t3)
    owner.add_task(t1)
    owner.add_task(t4)
    owner.add_task(t2)

    # Add two tasks at the same time to trigger conflict detection
    t5 = Task(type="Teeth Brush", time="09:00", pet=pet1)
    t6 = Task(type="Vet Call", time="09:00", pet=pet2)
    owner.add_task(t5)
    owner.add_task(t6)

    # Run lightweight conflict detection and print warnings
    warnings = owner.schedule.detect_conflicts()
    if warnings:
        for w in warnings:
            print(w)

    # Helper to print a list of tasks
    def print_tasks(title, tasks):
        print(title)
        for t in tasks:
            time_val = getattr(t, "time", None)
            try:
                time_str = time_val if isinstance(time_val, str) else time_val.strftime("%H:%M")
            except Exception:
                time_str = str(time_val)
            pet = getattr(t, "pet", None)
            pet_n = getattr(pet, "name", "Unknown") if pet else "NoPet"
            label = getattr(t, "type", getattr(t, "title", str(t)))
            status = "completed" if t.id in owner.schedule.archived_tasks else "pending"
            print(f"{time_str} - {pet_n} - {label} ({status})")
        print()

    # Print unsorted pending tasks
    print_tasks("All pending tasks (insertion order):", owner.schedule.get_pending_tasks())

    # Mark one task completed
    owner.change_task_status(t2.id, True)

    # Print sorted tasks by time
    sorted_tasks = owner.schedule.sort_by_time()
    print_tasks("Pending tasks sorted by time:", sorted_tasks)

    # Print completed tasks via filter
    completed = owner.schedule.filter_tasks(completed=True)
    print_tasks("Completed tasks:", completed)

    # Print tasks filtered by pet name
    fido_tasks = owner.schedule.filter_tasks(pet_name="Fido")
    print_tasks("Tasks for Fido (any status):", fido_tasks)