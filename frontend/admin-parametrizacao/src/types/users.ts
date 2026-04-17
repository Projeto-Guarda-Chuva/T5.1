export interface User {
  id: number;
  username: string;
  password: string;
  token: string;
}

export interface LoginEntry {
  username: string;
  password: string;
}
