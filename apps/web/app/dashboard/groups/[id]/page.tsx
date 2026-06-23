"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { API_URL } from "@/lib/auth";
import styles from "./page.module.css";

export default function GroupDetailPage() {
    const { id } = useParams<{ id: string }>();
    const searchParams = useSearchParams();
    const name = searchParams.get("name"); // passed as a query param when navigating from the groups list
    const router = useRouter();
    const [members, setMembers] = useState<any[]>([]);

    useEffect(() => {
        const fetchMembers = async () => {
            const response = await fetch(`${API_URL}/groups/${id}/members`, {
                credentials: "include"
            });
            if (response.ok) {
                const data = await response.json();
                setMembers(data);
            }
        };
        fetchMembers();
    }, [id]);

    const handleAssignFriend = async (friendId: number, friendName: string) => {
        const response = await fetch(`${API_URL}/groups/${id}/friend?friend_id=${friendId}`, {
            method: "POST",
            credentials: "include"
        });
        if (response.ok) {
            alert(`${friendName} is now your designated friend in this group.`);
        } else {
            alert("Could not assign friend. Please try again.");
        }
    };

    return (
        <main className = {styles.container}>
            <button className = {styles.back} onClick = {() => router.back()}>← Back</button>
            <h1 className = {styles.heading}>{name}</h1>
            <h2 className = {styles.sectionHeading}>Members</h2>
            {members.length === 0 && (
                <p className = {styles.empty}>No other members yet.</p>
            )}
            {members.map(member => (
                <div key = {member.user_id} className = {styles.memberRow}>
                    <p className = {styles.memberName}>{member.first_name}</p>
                    <button
                        className = {styles.button}
                        onClick = {() => handleAssignFriend(member.user_id, member.first_name)}
                    >
                        Set as friend
                    </button>
                </div>
            ))}
        </main>
    );
}