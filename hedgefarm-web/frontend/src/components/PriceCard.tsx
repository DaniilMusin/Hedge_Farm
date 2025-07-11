export default function PriceCard({ data }: { data: any }) {
  return (
    <div className="border p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Минимальная цена, ₽/кг</h2>
      <ul className="space-y-1">
        <li>Фьючерс: <b>{data.floor_futures}</b></li>
        <li>PUT‑опцион: <b>{data.floor_put}</b></li>
        <li>Форвард: <b>{data.floor_forward}</b></li>
      </ul>
      <p className="mt-2">Рекомендуем: <b className="text-green-600 uppercase">{data.recommended}</b></p>
    </div>
  )
}