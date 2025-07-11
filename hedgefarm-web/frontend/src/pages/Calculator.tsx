import { useState } from "react";
import api from "../api/axios";
import PriceCard from "../components/PriceCard";

export default function Calculator() {
  const [vol, setVol] = useState(1000);
  const [data, setData] = useState<any | null>(null);

  async function fetchPrice() {
    const res = await api.post("/price", { volume_t: vol });
    setData(res.data);
  }

  return (
    <div className="max-w-xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Калькулятор хеджирования</h1>
      <input type="number" value={vol}
        onChange={(e) => setVol(+e.target.value)}
        className="border p-2 w-full mb-3"/>
      <button onClick={fetchPrice}
        className="bg-green-600 text-white px-4 py-2 rounded mb-4">Рассчитать</button>
      {data && <PriceCard data={data}/>}
    </div>
  );
}