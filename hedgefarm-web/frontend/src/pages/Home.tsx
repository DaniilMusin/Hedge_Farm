import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="text-center py-16">
        <h1 className="text-4xl font-bold text-green-600 mb-4">HedgeFarm</h1>
        <p className="text-xl text-gray-600 mb-8">
          Умная платформа для хеджирования сельскохозяйственных рисков
        </p>
        <div className="space-x-4">
          <Link 
            to="/calculator" 
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 inline-block"
          >
            Рассчитать цены
          </Link>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-8 py-16">
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-4">Фьючерсы</h3>
          <p className="text-gray-600">Стандартизированные контракты на поставку товара в будущем</p>
        </div>
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-4">Опционы</h3>
          <p className="text-gray-600">Право купить или продать товар по фиксированной цене</p>
        </div>
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-4">Форварды</h3>
          <p className="text-gray-600">Индивидуальные договоры на поставку товара</p>
        </div>
      </div>
    </div>
  );
}