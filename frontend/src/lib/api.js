import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

export async function listTasks() {
  const res = await api.get(`/tasks`);
  return res.data;
}

export async function createTask(title) {
  const res = await api.post(`/tasks`, { title });
  return res.data;
}

export async function patchTaskCompletion(id, completed) {
  const res = await api.patch(`/tasks/${id}`, { completed });
  return res.data;
}

export async function deleteTask(id) {
  await api.delete(`/tasks/${id}`);
  return true;
}
