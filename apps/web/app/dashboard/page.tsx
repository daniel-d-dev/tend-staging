import Link from "next/link";

export default function DashboardPage() {
    return (
        <div>
            <h1>Dashboard</h1>
            <Link href = "/dashboard/checkin">Check in</Link>
            <Link href = "/dashboard/groups">Groups</Link>
            <Link href = "/dashboard/notifications">Notifications</Link>
        </div>
    );
}