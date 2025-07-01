export const revalidate = 60;
export const dynamic = "force-dynamic";

export default async function Home() {
  const res = await fetch("https://worldtimeapi.org/api/timezone/Etc/UTC", {
    next: { revalidate: 60 },
  });
  const data = await res.json();
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-2xl font-bold mb-4">Server Time</h1>
      <pre className="bg-gray-100 p-4 rounded">{JSON.stringify(data, null, 2)}</pre>
    </main>
  );
}
