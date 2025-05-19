import axios from 'axios';

// Create an Axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 30000, // Increased timeout to 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add a request interceptor to include JWT token in headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add the required subject field to all requests
    // This ensures all API calls have the subject field
    if (config.method === 'get' && !config.params) {
      config.params = { subject: "ApiRequest" };
    } else if (config.method === 'get' && config.params) {
      config.params.subject = config.params.subject || "ApiRequest";
    } else if (['post', 'put', 'patch'].includes(config.method)) {
      // For POST, PUT, PATCH requests, ensure the body has a subject property
      if (config.data && typeof config.data === 'object') {
        config.data = { ...config.data, subject: config.data.subject || "ApiRequest" };
      } else if (!config.data) {
        config.data = { subject: "ApiRequest" };
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Error response data:', error.response.data);
      console.error('Error response status:', error.response.status);
      
      if (error.response.status === 401) {
        // If unauthorized, redirect to login
        console.log('Unauthorized: You need to login again');
        localStorage.removeItem('token');
        // Only redirect if we're not already on the login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      } else if (error.response.status === 422) {
        // Handle the 422 UNPROCESSABLE ENTITY error specifically
        console.error('Validation error:', error.response.data);
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received from server. Request:', error.request);
      
      // Check if this is a timeout error
      if (error.code === 'ECONNABORTED') {
        console.warn('Retrying due to timeout...');
        return api(config);
      }
      else if (!error.response && error.message.includes('Network Error')) {
        console.error('Network error: Potential CORS or credentials issue.');
      }
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);

// Enhanced order-specific API methods
const orderAPI = {
  // Get all orders
  getOrders: () => api.get('/api/v1/orders'),
  
  // Get specific order
  getOrder: (orderId) => api.get(`/api/v1/orders/${orderId}`),
  
  // Update an order - more robust implementation
  updateOrder: async (orderId, orderData) => {
    console.log(`Updating order ${orderId} with data:`, orderData);
    
    try {
      // First try sending data directly
      return await api.put(`/api/v1/orders/${orderId}`, orderData);
    } catch (directError) {
      console.error('First update attempt failed:', directError);
      
      // Try with order wrapper
      try {
        return await api.put(`/api/v1/orders/${orderId}`, { order: orderData });
      } catch (wrappedError) {
        console.error('Second update attempt failed:', wrappedError);
        
        // Try with a slightly modified structure as last resort
        return await api.put(`/api/v1/orders/${orderId}`, { 
          subject: "ApiRequest",
          order: {
            ...orderData,
            subject: "OrderUpdate"
          }
        });
      }
    }
  },
  
  // Delete an order
  deleteOrder: (orderId) => api.delete(`/api/v1/orders/${orderId}`),
  
  // Create a new order
  createOrder: (orderData) => api.post('/api/v1/orders', orderData),
};

export { orderAPI };
export default api;