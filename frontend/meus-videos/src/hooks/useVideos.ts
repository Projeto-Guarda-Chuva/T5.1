import { useQuery } from "@tanstack/react-query";
import videosService, { Video } from "../services/videosService";

export const VIDEOS_QUERY_KEY = ["videos"] as const;

export function useVideos() {
  return useQuery<Video[]>({
    queryKey: VIDEOS_QUERY_KEY,
    queryFn: () => videosService.listVideos(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
