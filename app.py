import streamlit as st
from datetime import datetime
from pawpal_system import Owner, Pet, Task, Schedule

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
gender = st.selectbox("Gender", ["male", "female", "unknown"])

# initialize single-owner slot so UI handlers can use it
if "owner" not in st.session_state or not isinstance(st.session_state.get("owner"), Owner):
    st.session_state.owner = Owner(owner_name)
owner: Owner = st.session_state.owner

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# Add Pet button: call Owner.add_pet
if st.button("Add pet"):
    existing = next((p for p in owner.pets if p.name == pet_name), None)
    if not existing:
        new_pet = Pet(name=pet_name, type=species, gender=gender)
        owner.add_pet(new_pet)
        st.success(f"Added pet '{pet_name}'")
    else:
        st.info(f"Pet '{pet_name}' already exists")

# Add Task button: create Task and add to Owner's schedule
if st.button("Add task"):
    # try find pet object by name to associate task
    pet_obj = next((p for p in owner.pets if p.name == pet_name), None)
    task = Task(type=task_title, time=datetime.now(), pet=pet_obj)
    owner.add_task(task)
    # keep a lightweight UI record for display
    st.session_state.tasks.append(
        {"id": task.id, "title": task_title, "duration_minutes": int(duration), "priority": priority, "pet": pet_obj.name if pet_obj else None}
    )
    st.success(f"Added task '{task_title}'")

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    st.warning(
        "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
    )
    st.markdown(
        """
Suggested approach:
1. Design your UML (draft).
2. Create class stubs (no logic).
3. Implement scheduling behavior.
4. Connect your scheduler here and display results.
"""
    )

# Vault of owners keyed by owner name:
if "owners" not in st.session_state:
    st.session_state.owners = {}
owners: dict = st.session_state.owners

if owner_name not in owners or not isinstance(owners[owner_name], Owner):
    owners[owner_name] = Owner(owner_name)
owner_for_name: Owner = owners[owner_name]
