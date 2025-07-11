import axios from "axios";
export default axios.create({
  baseURL: "/api", // nginx проксирует на backend
});