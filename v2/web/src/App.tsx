import { Header } from "@/components/layout/header";
import { HomePage } from "@/pages/home";

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <HomePage />
    </div>
  );
}
