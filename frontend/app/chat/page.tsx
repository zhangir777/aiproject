import ChatInterface from '@/components/ChatInterface';

export const metadata = {
  title: 'AI-Чат — EnbekAI',
};

export default function ChatPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI-Чат</h1>
        <p className="text-gray-500 text-sm mt-1">
          Задайте вопрос о рынке труда Казахстана — AI ответит на основе реальных данных
        </p>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <ChatInterface />
      </div>
    </div>
  );
}
