import React, { useEffect, useMemo, useRef, useState } from "react";
import "@/App.css";

import { createTask, deleteTask, listTasks, patchTaskCompletion } from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}

function formatPercent(n) {
  return `${Math.round(n)}%`;
}

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const inputRef = useRef(null);

  const [focusMode, setFocusMode] = useState(false);
  const [saveState, setSaveState] = useState("idle"); // idle | saving | saved | error

  const completedCount = useMemo(
    () => tasks.filter((t) => t.completed).length,
    [tasks],
  );

  const totalCount = tasks.length;
  const percent = useMemo(() => {
    if (totalCount === 0) return 0;
    return clamp((completedCount / totalCount) * 100, 0, 100);
  }, [completedCount, totalCount]);

  const visibleTasks = useMemo(() => {
    if (!focusMode) return tasks;
    return tasks.filter((t) => !t.completed);
  }, [tasks, focusMode]);

  const allDone = totalCount > 0 && completedCount === totalCount;

  const setSavedSoon = () => {
    setSaveState("saved");
    window.clearTimeout(window.__taskBoardSaveTimeout);
    window.__taskBoardSaveTimeout = window.setTimeout(() => {
      setSaveState("idle");
    }, 1200);
  };

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listTasks();
      setTasks(data);
    } catch (e) {
      setError("Could not load tasks. Please refresh.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onAdd = async () => {
    const trimmed = title.trim();
    if (trimmed.length < 3) {
      setError("Task title must be at least 3 characters.");
      return;
    }

    setError("");
    setSaveState("saving");
    try {
      const res = await createTask(trimmed);
      setTasks((prev) => [...prev, res.task]);
      setTitle("");
      setSavedSoon();
      inputRef.current?.focus();
    } catch (e) {
      setSaveState("error");
      setError("Could not add task. Please try again.");
    }
  };

  const onToggle = async (task) => {
    setError("");
    setSaveState("saving");

    // optimistic update
    setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, completed: !t.completed } : t)));

    try {
      const res = await patchTaskCompletion(task.id, !task.completed);
      setTasks((prev) => prev.map((t) => (t.id === task.id ? res.task : t)));
      setSavedSoon();
    } catch (e) {
      setSaveState("error");
      setError("Could not update task. Please try again.");
      // revert
      setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, completed: task.completed } : t)));
    }
  };

  const onDelete = async (task) => {
    setError("");
    setSaveState("saving");

    const prev = tasks;
    setTasks((p) => p.filter((t) => t.id !== task.id));

    try {
      await deleteTask(task.id);
      setSavedSoon();
    } catch (e) {
      setSaveState("error");
      setError("Could not delete task. Please try again.");
      setTasks(prev);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter") onAdd();
    if (e.key === "Escape") {
      setTitle("");
      inputRef.current?.blur();
    }
  };

  return (
    <div
      className="min-h-screen bg-[radial-gradient(1200px_circle_at_20%_10%,rgba(99,102,241,0.25),transparent_50%),radial-gradient(900px_circle_at_80%_30%,rgba(16,185,129,0.18),transparent_45%),linear-gradient(to_bottom,rgba(3,7,18,1),rgba(2,6,23,1))] text-zinc-100"
      data-testid="task-board-page"
    >
      <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:py-14">
        <header className="mb-8 sm:mb-10">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1
                className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight"
                data-testid="app-title"
              >
                Task Board
              </h1>
              <p
                className="mt-3 max-w-2xl text-base md:text-lg text-zinc-300"
                data-testid="app-subtitle"
              >
                A lightweight board for your daily wins. Add, check off, and keep your focus.
              </p>
            </div>

            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-zinc-300" data-testid="focus-mode-label">
                  Focus Mode
                </span>
                <Switch
                  checked={focusMode}
                  onCheckedChange={setFocusMode}
                  data-testid="focus-mode-switch"
                />
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    saveState === "saving"
                      ? "secondary"
                      : saveState === "saved"
                        ? "default"
                        : saveState === "error"
                          ? "destructive"
                          : "outline"
                  }
                  className={
                    saveState === "saved"
                      ? "bg-emerald-500/15 text-emerald-100 border-emerald-400/30"
                      : saveState === "saving"
                        ? "bg-indigo-500/15 text-indigo-100 border-indigo-400/30"
                        : saveState === "error"
                          ? "bg-rose-500/15 text-rose-100 border-rose-400/30"
                          : "bg-white/5 text-zinc-200 border-white/10"
                  }
                  data-testid="save-indicator"
                >
                  {saveState === "saving"
                    ? "Saving…"
                    : saveState === "saved"
                      ? "Saved"
                      : saveState === "error"
                        ? "Not saved"
                        : "Ready"}
                </Badge>

                <Button
                  variant="ghost"
                  className="text-zinc-200 hover:text-white hover:bg-white/10"
                  onClick={load}
                  disabled={loading}
                  data-testid="refresh-button"
                >
                  Refresh
                </Button>
              </div>
            </div>
          </div>
        </header>

        {allDone ? (
          <div
            className="mb-6 rounded-xl border border-white/10 bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-indigo-500/15 px-5 py-4 glow-border pop-in"
            data-testid="all-done-banner"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="text-sm text-zinc-200" data-testid="all-done-kicker">
                  Progress 100%
                </div>
                <div
                  className="mt-0.5 text-base md:text-lg font-medium text-white"
                  data-testid="all-done-message"
                >
                  Everything’s done. Take a small victory lap.
                </div>
              </div>
              <div className="text-sm text-zinc-200" data-testid="all-done-side-note">
                Focus Mode can help keep it that way.
              </div>
            </div>
          </div>
        ) : null}

        <Card className="bg-white/5 border-white/10 text-zinc-100 glow-border" data-testid="task-board-card">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg" data-testid="task-board-card-title">
              Today’s Tasks
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex flex-col sm:flex-row gap-3">
              <Input
                ref={inputRef}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Add a task (min 3 chars)…"
                className="bg-black/20 border-white/10 text-zinc-100 placeholder:text-zinc-500"
                data-testid="add-task-input"
              />
              <Button
                onClick={onAdd}
                className="rounded-full bg-indigo-500 hover:bg-indigo-400 text-white px-6"
                data-testid="add-task-button"
              >
                Add Task
              </Button>
            </div>

            {error ? (
              <div
                className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-rose-100"
                data-testid="error-message"
              >
                {error}
              </div>
            ) : null}

            <div className="space-y-2" data-testid="progress-section">
              <div className="flex items-center justify-between gap-4">
                <div className="text-sm text-zinc-300" data-testid="progress-label">
                  Progress
                </div>
                <div className="text-sm text-zinc-200" data-testid="progress-text">
                  {formatPercent(percent)} ({completedCount}/{totalCount})
                </div>
              </div>
              <Progress
                value={percent}
                className="h-2 bg-white/10"
                data-testid="progress-bar"
              />
            </div>

            <Separator className="bg-white/10" data-testid="tasks-separator" />

            {loading ? (
              <div className="text-sm text-zinc-300" data-testid="loading-message">
                Loading tasks…
              </div>
            ) : visibleTasks.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-6" data-testid="empty-state">
                <div className="text-base font-medium text-zinc-100" data-testid="empty-state-title">
                  {tasks.length === 0 ? "No tasks yet." : "Nothing left to focus on."}
                </div>
                <div className="mt-1 text-sm text-zinc-300" data-testid="empty-state-subtitle">
                  {tasks.length === 0
                    ? "Add your first task above. Tip: press Enter to add quickly."
                    : "Focus Mode is hiding completed tasks."}
                </div>

                {tasks.length > 0 && focusMode ? (
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <Button
                      variant="secondary"
                      className="rounded-full bg-white/10 hover:bg-white/15 text-zinc-100"
                      onClick={() => setFocusMode(false)}
                      data-testid="empty-state-show-completed-button"
                    >
                      Show completed
                    </Button>
                  </div>
                ) : null}
              </div>
            ) : (
              <ul className="space-y-2" data-testid="task-list">
                {visibleTasks.map((t) => (
                  <li
                    key={t.id}
                    className="group flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/20 px-3 py-3"
                    data-testid={`task-row-${t.id}`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Checkbox
                        checked={t.completed}
                        onCheckedChange={() => onToggle(t)}
                        className="border-white/20"
                        data-testid={`task-complete-checkbox-${t.id}`}
                      />
                      <div className="min-w-0">
                        <div
                          className={
                            "text-base text-zinc-100 truncate " +
                            (t.completed ? "line-through text-zinc-400" : "")
                          }
                          title={t.title}
                          data-testid={`task-title-${t.id}`}
                        >
                          {t.title}
                        </div>
                        <div
                          className="text-xs text-zinc-500"
                          data-testid={`task-meta-${t.id}`}
                        >
                          {t.completed ? "Completed" : "Active"}
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      onClick={() => onDelete(t)}
                      className="rounded-full text-zinc-200 hover:text-white hover:bg-white/10"
                      data-testid={`task-delete-button-${t.id}`}
                    >
                      Delete
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <footer className="mt-10 text-sm text-zinc-500" data-testid="app-footer">
          Tip: Enter adds, Esc clears. Focus Mode hides completed tasks.
        </footer>
      </div>
    </div>
  );
}
