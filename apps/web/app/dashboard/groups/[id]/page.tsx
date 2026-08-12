"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { API_URL } from "@/lib/auth";
import styles from "./page.module.css";

export default function GroupDetailPage() {
    const { id } = useParams<{ id: string }>();
    const searchParams = useSearchParams();
    const name = searchParams.get("name"); // passed as query params when navigating from the groups list
    const createdBy = searchParams.get("createdBy");
    const router = useRouter();
    const [members, setMembers] = useState<any[]>([]);
    const [groupName, setGroupName] = useState(name ?? "");
    const [editingName, setEditingName] = useState(false);
    const [savingName, setSavingName] = useState(false);
    const [isCreator, setIsCreator] = useState(false);

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
        const checkIsCreator = async () => {
            const response = await fetch(`${API_URL}/auth/me`, {
                credentials: "include"
            });
            if (response.ok) {
                const me = await response.json();
                setIsCreator(String(me.id) === createdBy);
            }
        };
        fetchMembers();
        checkIsCreator();
    }, [id]);

    const handleRename = async () => {
        if (!groupName.trim()) {
            alert("Group name can't be empty.");
            return;
        }
        setSavingName(true);
        const response = await fetch(`${API_URL}/groups/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ name: groupName.trim() })
        });
        setSavingName(false);
        if (response.ok) {
            setEditingName(false);
        } else {
            let message = "Could not rename group. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            alert(message);
        }
    };

    const handleDelete = async () => {
        if (!confirm(`Are you sure you want to delete "${groupName}"? This can't be undone.`)) {
            return;
        }
        const response = await fetch(`${API_URL}/groups/${id}`, {
            method: "DELETE",
            credentials: "include"
        });
        if (response.ok) {
            router.replace("/dashboard/groups");
        } else {
            alert("Could not delete group. Please try again.");
        }
    };

    const handleAssignFriend = async (friendId: number, friendName: string) => {
        const response = await fetch(`${API_URL}/groups/${id}/friend?friend_id=${friendId}`, {
            method: "POST",
            credentials: "include"
        });
        if (response.ok) {
            alert(`${friendName} is now your designated friend in this group.`);
        } else {
            let message = "Could not assign friend. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            alert(message);
        }
    };

    return (
        <main className = {styles.container}>
            <button className = {styles.back} onClick = {() => router.back()}>← Back</button>
            {editingName ? (
                <div className = {styles.renameRow}>
                    <input
                        className = {styles.renameInput}
                        value = {groupName}
                        onChange = {(e) => setGroupName(e.target.value)}
                        autoFocus
                    />
                    <button className = {styles.button} onClick = {handleRename} disabled = {savingName}>
                        {savingName ? "Saving..." : "Save"}
                    </button>
                </div>
            ) : (
                <div className = {styles.renameRow}>
                    <h1 className = {styles.heading}>{groupName}</h1>
                    {isCreator && (
                        <button className = {styles.editLink} onClick = {() => setEditingName(true)}>Rename</button>
                    )}
                </div>
            )}
            {isCreator && (
                <button className = {styles.deleteLink} onClick = {handleDelete}>Delete group</button>
            )}
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
            <button
                className = {styles.button}
                onClick = {() => router.push(`/dashboard/groups/${id}/feed?name=${name}`)}
            >
                Group feed
            </button>
        </main>
    );
}