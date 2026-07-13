"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { API_URL } from "@/lib/auth";
import styles from "./page.module.css";

type ReactionData = {
    id: number;
    post_id: number;
    user_id: number;
    emoji: string;
};

type PostData = {
    id: number;
    group_id: number;
    author_id: number | null;
    author_name: string | null;
    content: string;
    author_type: string;
    parent_post_id: number | null;
    parent_author: string | null;
    parent_content: string | null;
    created_at: string;
    reactions: ReactionData[];
};

const EMOJIS = ["❤️", "👍", "😔", "💪", "🙏"];

export default function FeedPage() {
    const { id } = useParams<{ id: string }>();
    const searchParams = useSearchParams();
    const name = searchParams.get("name");
    const router = useRouter();
    const [posts, setPosts] = useState<PostData[]>([]);
    const [newPost, setNewPost] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [replyingTo, setReplyingTo] = useState<number | null>(null);
    const [currentUserId, setCurrentUserId] = useState<number | null>(null);
    const [openPickerPostId, setOpenPickerPostId] = useState<number | null>(null);

    const fetchFeed = async () => {
        const [feedResponse, meResponse] = await Promise.all([ // we need the user's id to know which reactions are theirs
            fetch(`${API_URL}/feed/groups/${id}`, { credentials: "include" }),
            fetch(`${API_URL}/auth/me`, { credentials: "include" })
        ]);
        if (feedResponse.ok) {
            const data = await feedResponse.json();
            setPosts(data);
        }
        if (meResponse.ok) {
            const me = await meResponse.json();
            setCurrentUserId(me.id);
        }
    };

    useEffect(() => {
        fetchFeed();
    }, [id]);

    const handlePost = async () => {
        if (!newPost.trim()) return;
        setSubmitting(true);
        let url = `${API_URL}/feed/groups/${id}`;
        if (replyingTo) {
            url = `${API_URL}/feed/posts/${replyingTo}/reply`;
        }
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ content: newPost.trim() })
        });
        setSubmitting(false);
        if (response.ok) {
            setNewPost("");
            setReplyingTo(null);
            fetchFeed();
        }
    };

    const handleReact = async (postId: number, emoji: string, alreadyReacted: boolean) => {
        if (alreadyReacted) {
            await fetch(`${API_URL}/feed/posts/${postId}/react?emoji=${emoji}`, {
                method: "DELETE",
                credentials: "include"
            });
        } else {
            await fetch(`${API_URL}/feed/posts/${postId}/react`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ emoji })
            });
        }
        fetchFeed();
    };

    return (
        <main className = {styles.container}>
            <button className = {styles.back} onClick = {() => router.back()}>← Back</button>
            <h1 className = {styles.heading}>{name}</h1>
            <div className = {styles.feed}>
                {posts.map(post => {
                    const isAgent = post.author_type === "agent";
                    let authorDisplay = post.author_name;
                    if (isAgent) {
                        authorDisplay = "Thread"; // agent posts surface as system messages and are not attributed to a person
                    }
                    return (
                        <div key = {post.id} className = {`${styles.post} ${isAgent ? styles.agentPost : ""}`}>
                            <p className = {`${styles.author} ${isAgent ? styles.agentAuthor : ""}`}>{authorDisplay}</p>
                            {post.parent_content && (
                                <div className = {styles.replyContext}>
                                    <p className = {styles.replyContextText}>↳ {post.parent_author}: {post.parent_content}</p>
                                </div>
                            )}
                            <p className = {styles.content}>{post.content}</p>
                            <p className = {styles.timestamp}>
                                {new Date(post.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                            </p>
                            <div className = {styles.reactions}>
                                {post.reactions
                                    .filter((r, index, self) => self.findIndex(x => x.emoji === r.emoji) === index) // if multiple people reacted with the same emoji, only keep the first occurrence but show the count separately
                                    .map(r => {
                                        const count = post.reactions.filter(x => x.emoji === r.emoji).length;
                                        const reacted = post.reactions.some(x => x.emoji === r.emoji && x.user_id === currentUserId);
                                        return (
                                            <button
                                                key = {r.emoji}
                                                className = {`${styles.emojiButton} ${reacted ? styles.emojiActive : ""}`}
                                                onClick = {() => handleReact(post.id, r.emoji, reacted)}
                                            >
                                                {r.emoji} {count}
                                            </button>
                                        );
                                    })
                                }
                                {openPickerPostId === post.id && (
                                    <div className = {styles.emojiPicker}>
                                        {EMOJIS.map(emoji => (
                                            <button
                                                key = {emoji}
                                                className = {styles.emojiPickerOption}
                                                onClick = {() => {
                                                    const reacted = post.reactions.some(r => r.emoji === emoji && r.user_id === currentUserId);
                                                    handleReact(post.id, emoji, reacted);
                                                    setOpenPickerPostId(null);
                                                }}
                                            >
                                                {emoji}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                <button
                                    className = {styles.addReaction}
                                    onClick = {() => setOpenPickerPostId(openPickerPostId === post.id ? null : post.id)}
                                >
                                    +
                                </button>
                            </div>
                            {!post.parent_post_id && ( // only top level posts get a reply button. Can't reply to a reply
                                <button className = {styles.replyButton} onClick = {() => setReplyingTo(post.id)}>Reply</button>
                            )}
                        </div>
                    );
                })}
            </div>
            {replyingTo && (
                <p className = {styles.replyingLabel}>
                    Replying to a post: <span className = {styles.cancel} onClick = {() => setReplyingTo(null)}>cancel</span>
                </p>
            )}
            <div className = {styles.inputRow}>
                <textarea
                    className = {styles.input}
                    placeholder = {replyingTo ? "Write a reply..." : "Write something..."}
                    value = {newPost}
                    onChange = {(e) => setNewPost(e.target.value)}
                    rows = {3}
                />
                <button
                    className = {styles.sendButton}
                    onClick = {handlePost}
                    disabled = {submitting}
                >
                    Post
                </button>
            </div>
        </main>
    );
}