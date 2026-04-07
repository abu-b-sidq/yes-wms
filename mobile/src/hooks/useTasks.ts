import { useState, useCallback } from 'react';
import {
  PickTask,
  DropTask,
  getAvailableTasks,
  getMyTasks,
  claimPickTask,
  claimDropTask,
  startPickTask,
  completePickTask,
  startDropTask,
  completeDropTask,
} from '../api/tasks';

type TaskLists<TPick, TDrop> = {
  picks?: TPick[] | null;
  drops?: TDrop[] | null;
};

type TaskResponse<TPick, TDrop> = {
  data?: TaskLists<TPick, TDrop> | null;
};

function ensureTaskList<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function getTaskLists<TPick, TDrop>(
  response: TaskResponse<TPick, TDrop> | null | undefined
) {
  return {
    picks: ensureTaskList(response?.data?.picks),
    drops: ensureTaskList(response?.data?.drops),
  };
}

export function useTasks() {
  const [availablePicks, setAvailablePicks] = useState<PickTask[]>([]);
  const [availableDrops, setAvailableDrops] = useState<DropTask[]>([]);
  const [myPicks, setMyPicks] = useState<PickTask[]>([]);
  const [myDrops, setMyDrops] = useState<DropTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [available, mine] = await Promise.all([
        getAvailableTasks(),
        getMyTasks(),
      ]);
      const availableTasks = getTaskLists<PickTask, DropTask>(available);
      const myTasks = getTaskLists<PickTask, DropTask>(mine);
      setAvailablePicks(availableTasks.picks);
      setAvailableDrops(availableTasks.drops);
      setMyPicks(myTasks.picks);
      setMyDrops(myTasks.drops);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const claim = useCallback(async (pickId: string) => {
    const result = await claimPickTask(pickId);
    await refresh();
    return result.data;
  }, [refresh]);

  const claimDrop = useCallback(async (dropId: string) => {
    const result = await claimDropTask(dropId);
    await refresh();
    return result.data;
  }, [refresh]);

  const startPick = useCallback(async (pickId: string) => {
    const result = await startPickTask(pickId);
    await refresh();
    return result.data;
  }, [refresh]);

  const completePick = useCallback(async (pickId: string) => {
    const result = await completePickTask(pickId);
    await refresh();
    return result.data;
  }, [refresh]);

  const startDrop = useCallback(async (dropId: string) => {
    const result = await startDropTask(dropId);
    await refresh();
    return result.data;
  }, [refresh]);

  const completeDrop = useCallback(async (dropId: string) => {
    const result = await completeDropTask(dropId);
    await refresh();
    return result.data;
  }, [refresh]);

  return {
    availablePicks,
    availableDrops,
    myPicks,
    myDrops,
    loading,
    error,
    refresh,
    claim,
    claimDrop,
    startPick,
    completePick,
    startDrop,
    completeDrop,
  };
}
