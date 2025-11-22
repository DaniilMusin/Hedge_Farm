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

export default function PriceCard({ data }: { data: PriceData }) {
  const formatPrice = (price: number) => price.toFixed(2);

  return (
    <div className="border p-4 rounded shadow bg-white">
      <h2 className="font-semibold mb-2 text-lg">Минимальная гарантированная цена, ₽/кг</h2>
      <ul className="space-y-2">
        <li className="flex justify-between">
          <span>Фьючерс:</span>
          <b className="text-blue-600">{formatPrice(data.floor_futures_rubkg)}</b>
        </li>
        <li className="flex justify-between">
          <span>PUT-опцион:</span>
          <b className="text-purple-600">{formatPrice(data.floor_put_rubkg)}</b>
        </li>
        <li className="flex justify-between">
          <span>Форвард:</span>
          <b className="text-orange-600">{formatPrice(data.floor_forward_rubkg)}</b>
        </li>
      </ul>
      <div className="mt-4 pt-3 border-t">
        <p className="text-sm text-gray-600">
          Рекомендуем: <b className="text-green-600 uppercase text-base">{data.recommended}</b>
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Расчет для {data.volume_t} тонн на срок {data.term_m} мес.
        </p>
      </div>
    </div>
  );
}