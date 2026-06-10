export const API_URL = "http://localhost:8000";

export async function getMe() {
    const response = await fetch(`${API_URL}/auth/me`, {
        credentials: "include"
    });
    if (!response.ok) return null;
    return response.json()
}
