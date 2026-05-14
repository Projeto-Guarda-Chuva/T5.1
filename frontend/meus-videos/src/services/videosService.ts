import api from "../api";

export interface Video {
  id: string;
  date: string;
  thumbnail: string;
  src: string;
}

export interface BackendVideoResponse {
  id: string;
  title: string;
  created_at: string;
  duration_seconds: number;
  thumbnail_url: string;
  video_url: string;
  status: string;
}

export interface VideoListResponse {
  items: BackendVideoResponse[];
  total: number;
  message: string;
}

const listVideos = async (): Promise<Video[]> => {
  const response = await api.get<VideoListResponse>("/videos");
  const items = response.data.items || [];

  // Transforma o formato do backend para o formato do frontend
  return items.map((video) => ({
    id: video.id,
    date: video.created_at, // Usa o created_at como date
    thumbnail: video.thumbnail_url,
    src: video.video_url,
  }));
};

export default {
  listVideos,
};
