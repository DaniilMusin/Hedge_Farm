import { useState } from "react";
import api from "../api/axios";
import PriceCard from "../components/PriceCard";

interface PriceData {
  floor_futures_rubkg: number;
  floor_put_rubkg: number;
  floor_forward_rubkg: number;
  recommended: string;
  culture: string;
  volume_t: number;
  term_m: number;
  calculated_at: string;
}

export default function Calculator() {
  const [vol, setVol] = useState(1000);
  const [termMonths, setTermMonths] = useState(6);
  const [data, setData] = useState<PriceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchPrice() {
    // Валидация
    if (vol <= 0) {
      setError("Объем должен быть положительным числом");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.post("/price", {
        culture: "wheat",
        volume_t: vol,
        term_m: termMonths
      });
      setData(res.data);
    } catch (err: any) {
      console.error("API Error:", err);
      const errorMessage = err.response?.data?.detail || "Ошибка при расчете цены. Попробуйте позже.";
      setError(errorMessage);
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Калькулятор хеджирования</h1>

      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">Объем (тонн)</label>
        <input
          type="number"
          value={vol}
          onChange={(e) => setVol(Number(e.target.value))}
          className="border p-2 w-full rounded"
          min="1"
          max="1000000"
        />
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium mb-1">Срок (месяцев)</label>
        <input
          type="number"
          value={termMonths}
          onChange={(e) => setTermMonths(Number(e.target.value))}
          className="border p-2 w-full rounded"
          min="1"
          max="12"
        />
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <button
        onClick={fetchPrice}
        disabled={loading}
        className={`w-full px-4 py-2 rounded mb-4 ${
          loading
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-green-600 hover:bg-green-700 text-white"
        }`}
      >
        {loading ? "Расчет..." : "Рассчитать"}
      </button>

      {data && <PriceCard data={data} />}
    </div>
  );
}