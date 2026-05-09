import streamlit as st

def display_dag_status(status_snapshot):
    """Menampilkan status setiap agent."""
    for agent, status in status_snapshot.items():
        color = "green" if status == "done" else "red" if status == "failed" else "blue" if status == "running" else "gray"
        st.markdown(f"- **{agent}**: :{color}[{status.upper()}]")

def display_progress_bar(completed, total, label):
    """Menampilkan progress bar eksekusi."""
    if total > 0:
        progress = completed / total
        st.progress(progress, text=f"{label}: {completed}/{total}")
    else:
        st.progress(0, text=label)

def display_agent_output(agent_name, output):
    """Menampilkan hasil eksekusi agent."""
    if hasattr(output, "dict"):
        st.json(output.dict())
    else:
        st.write(output)
