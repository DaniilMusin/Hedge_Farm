import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-green-600 text-white p-4">
      <div className="max-w-6xl mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">HedgeFarm</Link>
        <div className="space-x-4">
          <Link to="/" className="hover:text-green-200">Главная</Link>
          <Link to="/calculator" className="hover:text-green-200">Калькулятор</Link>
        </div>
      </div>
    </nav>
  );
}