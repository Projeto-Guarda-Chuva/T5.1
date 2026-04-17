const TOKEN_KEY = "token";

const setToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

export default {
  setToken,
  getToken,
  removeToken,
};
