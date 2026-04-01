from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

def _normalize_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%H:%M", "%Y-%m-%d %H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.max

@dataclass
class Pet:
    name: str
    type: str
    gender: str


@dataclass
class Task:
    """A scheduled activity for a pet, optionally recurring and prioritized."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    time: Any = field(default_factory=datetime.now)
    priority: int = 0
    completed: bool = False
    pet: Optional[Pet] = None

    def mark_completed(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as incomplete."""
        self.completed = False


@dataclass
class Schedule:
    """Active task manager with pending/completed storage and scheduling utilities."""
    tasks: List[Task] = field(default_factory=list)
    tasks_by_id: Dict[str, Task] = field(default_factory=dict)
    archived_tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add a new active task to the schedule unless it already exists."""
        if task.id in self.tasks_by_id or task.id in self.archived_tasks:
            return
        self.tasks.append(task)
        self.tasks_by_id[task.id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by id from active or archived collections."""
        return self.tasks_by_id.get(task_id) or self.archived_tasks.get(task_id)

    def set_task_completed(self, task_id: str) -> bool:
        """Mark an active task completed and move it to the archive.
        If the task has a 'daily' or 'weekly' frequency, create the next occurrence.
        """
        task = self.tasks_by_id.get(task_id)
        if not task:
            return False
        freq = getattr(task, "frequency", None)
        task.mark_completed()
        # move to archive
        try:
            self.tasks.remove(task)
        except ValueError:
            pass
        del self.tasks_by_id[task_id]
        self.archived_tasks[task_id] = task

        # If recurring, create next instance
        if isinstance(freq, str) and freq.lower() in ("daily", "weekly"):
            next_time = _advance_time_for_frequency(task.time, freq)
            new_task = Task(
                type=task.type,
                time=next_time,
                pet=task.pet,
                frequency=task.frequency,
            )
            # keep as pending (not completed)
            self.add_task(new_task)
        return True

    def set_task_incomplete(self, task_id: str) -> bool:
        """Restore an archived task to active (mark incomplete)."""
        task = self.archived_tasks.get(task_id)
        if not task:
            return False
        task.mark_incomplete()
        del self.archived_tasks[task_id]
        self.tasks.append(task)
        self.tasks_by_id[task_id] = task
        return True

    def remove_completed(self) -> List[Task]:
        """Permanently remove and return all archived (completed) tasks."""
        removed = list(self.archived_tasks.values())
        self.archived_tasks.clear()
        return removed

    def delete_archived(self, task_id: str) -> bool:
        """Delete a specific archived task by id."""
        if task_id in self.archived_tasks:
            del self.archived_tasks[task_id]
            return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """Return a list of currently active (pending) tasks."""
        return list(self.tasks)

    def get_completed_tasks(self) -> List[Task]:
        """Return a list of archived (completed) tasks."""
        return list(self.archived_tasks.values())

    def filter_tasks(self, completed: Optional[bool] = None, pet_name: Optional[str] = None) -> List[Task]:
        """Return tasks filtered by completion status and/or pet name.

        - completed: True => archived only, False => active only, None => both.
        - pet_name: case-insensitive match against task.pet.name or task.pet.nickname.
        """
        if completed is True:
            candidates = list(self.archived_tasks.values())
        elif completed is False:
            candidates = list(self.tasks)
        else:
            candidates = list(self.tasks) + list(self.archived_tasks.values())

        if pet_name is None:
            return candidates

        pn = pet_name.lower()

        def pet_matches(task: Task) -> bool:
            pet = getattr(task, "pet", None)
            if not pet:
                return False
            for attr in ("name", "nickname"):
                val = getattr(pet, attr, None)
                if isinstance(val, str) and val.lower() == pn:
                    return True
            return False

        return [t for t in candidates if pet_matches(t)]

    def sort_by_time(self, reverse: bool = False) -> List[Task]:
        """Return tasks sorted by their time attribute (earliest first by default)."""
        return sorted(self.tasks, key=lambda t: _to_time_obj(getattr(t, "time", None)), reverse=reverse)

    def sort_by_priority(self, reverse: bool = False) -> List[Task]:
        """Sort tasks by priority descending, then by scheduled time ascending."""
        return sorted(self.tasks, key=_task_priority_key, reverse=reverse)

    def detect_conflicts(self) -> List[str]:
        """Return warnings for active tasks that share the same time."""
        groups: Dict[str, List[Task]] = {}
        for task in self.tasks:
            time_key = (
                task.time.strftime("%H:%M")
                if isinstance(task.time, datetime)
                else str(task.time)
            )
            groups.setdefault(time_key, []).append(task)

        warnings: List[str] = []
        for time_key, tasks in groups.items():
            if len(tasks) > 1:
                labels = ", ".join(
                    f"{t.type}(pet={t.pet.name if t.pet else 'Unassigned'})"
                    for t in tasks
                )
                warnings.append(f"Warning: conflict at {time_key}: {labels}")
        return warnings


@dataclass
class Owner:
    name: str
    schedule: Schedule = field(default_factory=Schedule)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's pet list."""
        self.pets.append(pet)

    def add_task(self, task: Task) -> None:
        """Add a task to the owner's schedule."""
        self.schedule.add_task(task)

    def view_tasks(self, completed: Optional[bool] = None) -> List[Task]:
        """View pending, completed, or all tasks depending on 'completed' arg."""
        if completed is None:
            return self.schedule.get_pending_tasks() + self.schedule.get_completed_tasks()
        return self.schedule.get_completed_tasks() if completed else self.schedule.get_pending_tasks()

    def change_task_status(self, task_id: str, completed: bool) -> bool:
        """Change a task's status between completed and incomplete."""
        if completed:
            return self.schedule.set_task_completed(task_id)
        return self.schedule.set_task_incomplete(task_id)
