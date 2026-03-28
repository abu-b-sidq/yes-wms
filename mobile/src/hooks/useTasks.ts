import { useState, useCallback } from 'react';
import {
  PickTask,
  DropTask,
  getAvailableTasks,
  getMyTasks,
  claimPickTask,
  startPickTask,
  completePickTask,
  startDropTask,
  completeDropTask,
} from '../api/tasks';

export function useTasks() {
  const [availableTasks, setAvailableTasks] = useState<PickTask[]>([]);
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
      setAvailableTasks(available.data);
      setMyPicks(mine.data.picks);
      setMyDrops(mine.data.drops);
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
    availableTasks,
    myPicks,
    myDrops,
    loading,
    error,
    refresh,
    claim,
    startPick,
    completePick,
    startDrop,
    completeDrop,
  };
}
