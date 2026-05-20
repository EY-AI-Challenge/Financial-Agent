import { useEffect, useState } from 'react';
import apiClient from '../services/apiClient';

function Dashboard() {
    const [portfolio, setPortfolio] = useState(null);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // The apiClient will automatically handle the auth header
                const portfolioResponse = await apiClient.get('/api/portfolio/');
                setPortfolio(portfolioResponse.data);

                const userResponse = await apiClient.get('/api/users/me');
                setUser(userResponse.data);

            } catch (error) {
                console.error('Failed to fetch data', error);
                // Handle 401 Unauthorized, maybe redirect to login
            }
        };
        fetchData();
    }, []);

    return (
        <div>
            <h2>Dashboard</h2>
            {user ? <h3>Welcome, {user.username}!</h3> : <p>Loading user...</p>}
            
            <h3>Your Portfolio</h3>
            {portfolio ? <pre>{JSON.stringify(portfolio, null, 2)}</pre> : <p>Loading portfolio...</p>}
        </div>
    );
}
export default Dashboard;
