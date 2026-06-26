import Link from "next/link";
import styles from "./page.module.css";

export default function DashboardPage() {
    return (
        <div className={styles.container}>
            <h1 className={styles.heading}>Dashboard</h1>
            <div className={styles.grid}>
                <Link href="/dashboard/checkin" className={styles.card}>
                    <h2 className={styles.cardTitle}>Check in</h2>
                    <p className={styles.cardDescription}>Record how you are feeling today</p>
                </Link>
                <Link href="/dashboard/groups" className={styles.card}>
                    <h2 className={styles.cardTitle}>Groups</h2>
                    <p className={styles.cardDescription}>Manage your friend groups</p>
                </Link>
                <Link href="/dashboard/notifications" className={styles.card}>
                    <h2 className={styles.cardTitle}>Notifications</h2>
                    <p className={styles.cardDescription}>See nudges about your friends</p>
                </Link>
                <Link href="/dashboard/temperature" className={styles.card}>
                    <h2 className={styles.cardTitle}>Temperature Check</h2>
                    <p className={styles.cardDescription}>View your emotional trends over time</p>
                </Link>
            </div>
        </div>
    );
}