import { useState } from 'react';
import apiClient from '../services/apiClient';
import { useNavigate } from 'react-router-dom';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleLogin = async () => {
        // The backend expects form data for the token endpoint
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            // Correct endpoint and payload
            const response = await apiClient.post('/api/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });
            
            // The token is inside `access_token`
            localStorage.setItem('token', response.data.access_token);
            alert('Login successful!');
            navigate('/dashboard'); // Redirect to dashboard on success
        } catch (error) {
            console.error('Login failed', error);
            alert('Login failed! Check console for details.');
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
            <button onClick={handleLogin}>Log In</button>
        </div>
    );
}
export default Login;
