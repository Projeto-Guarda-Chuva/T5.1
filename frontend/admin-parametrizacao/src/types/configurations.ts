export interface ConfigurationParameters {
  movement_speed: number;
  movement_duration_seconds: number;
  video_capture_enabled: boolean;
  audio_capture_enabled: boolean;
}

export interface Configuration {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  parameters?: ConfigurationParameters;
}

export interface CreateConfigurationPayload {
  name: string;
  description: string;
  is_active: false;
  parameters: ConfigurationParameters;
}

export interface ConfigurationResponse {
  items: Configuration[];
  total: number;
  message: string;
}

export interface CurrentConfigurationResponse {
  configuration: Configuration;
  source: string;
  has_active_configuration: boolean;
  message: string;
}
