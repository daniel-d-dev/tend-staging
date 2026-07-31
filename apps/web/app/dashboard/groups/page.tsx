"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { API_URL } from "@/lib/auth";

export default function GroupsPage() {
    const [groups, setGroups] = useState<any[]>([]);
    const [groupName, setGroupName] = useState("");
    const [joinCode, setJoinCode] = useState("");
    const [creating, setCreating] = useState(false);
    const [joining, setJoining] = useState(false);
    const router = useRouter();

    const fetchGroups = async () => {
        const response = await fetch(`${API_URL}/groups/me`, {
            credentials: "include"
        });
        if (response.ok) {
            const data = await response.json();
            setGroups(data);
        }
    };

    useEffect(() => {
        fetchGroups();
    }, []);

    const handleCreateGroup = async () => {
        if (!groupName.trim()) {
            alert("Please enter a group name.");
            return;
        }
        setCreating(true);
        const response = await fetch(`${API_URL}/groups/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ name: groupName.trim() })
        });
        setCreating(false);
        if (response.ok) {
            setGroupName("");
            const data = await response.json();
            setGroups(prev => [...prev, data]);
        } else {
            let message = "Could not create group. Please try again.";
            try {
                const errorData = await response.json();
                if (errorData.detail) message = errorData.detail;
            } catch {
                // response body wasn't valid JSON, fall back to the generic message above
            }
            alert(message);
        }
    };

    const handleJoinGroup = async () => {
        if (!joinCode.trim()) {
            alert("Please enter a join code.");
            return;
        }
        setJoining(true);
        const response = await fetch(`${API_URL}/groups/join?join_code=${joinCode.trim().toUpperCase()}`, {
            method: "POST",
            credentials: "include"
        });
        setJoining(false);
        if (response.ok) {
            setJoinCode("");
            fetchGroups();
        } else {
            let message = "Could not join group. Please try again.";
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
            <h1 className = {styles.heading}>My Groups</h1>

            {groups.length === 0 && (
                <p className = {styles.empty}>You are not in any groups yet.</p>
            )}

            {groups.map(group => (
                <div
                    key = {group.id}
                    className = {styles.groupCard}
                    onClick = {() => router.push(`/dashboard/groups/${group.id}?name=${group.name}`)}
                    style = {{ cursor: "pointer" }}
                >
                    <p className = {styles.groupName}>{group.name}</p>
                    <p className = {styles.joinCode}>Join code: {group.join_code}</p>
                </div>
            ))}

            <h2 className = {styles.sectionHeading}>Create a group</h2>
            <p className = {styles.sectionDescription}>Choose a name for your group</p>
            <input
                className = {styles.input}
                placeholder = "Group name"
                value = {groupName}
                onChange = {(e) => setGroupName(e.target.value)}
            />
            <button
                className = {styles.button}
                onClick = {handleCreateGroup}
                disabled = {creating}
            >
                {(() => {
                    if (creating) return "Creating...";
                    return "Create group";
                })()}
            </button>

            <h2 className = {styles.sectionHeading}>Join a group</h2>
            <p className = {styles.sectionDescription}>Ask a friend for their group's join code</p>
            <input
                className = {styles.input}
                placeholder = "Enter join code"
                value = {joinCode}
                onChange = {(e) => setJoinCode(e.target.value)}
            />
            <button
                className = {styles.button}
                onClick = {handleJoinGroup}
                disabled = {joining}
            >
                {(() => {
                    if (joining) return "Joining...";
                    return "Join group";
                })()}
            </button>
        </main>
    );
}