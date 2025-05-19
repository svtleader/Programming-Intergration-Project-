import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const OrderDetailPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [orderItems, setOrderItems] = useState([]);
  const [notification, setNotification] = useState({ show: false, itemId: null, message: '' });
  const [saveStatus, setSaveStatus] = useState({ saving: false, success: false, error: false });
  const [debugInfo, setDebugInfo] = useState(null);

  useEffect(() => {
    fetchOrderDetails();
  }, [orderId]);

  const fetchOrderDetails = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/orders/${orderId}`);
      setOrder(response.data.order);

      if (response.data.order && response.data.order.OrderDetails) {
        setOrderItems(response.data.order.OrderDetails.map(item => ({
          ...item,
          quantity: item.Quantity,
          totalPrice: item.Price * item.Quantity
        })));
      }
    } catch (err) {
      setError('Failed to fetch order details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const calculateOrderTotal = () => {
    return orderItems.reduce((total, item) => total + item.totalPrice, 0);
  };

  const handleQuantityChange = (itemId, newQuantity) => {
    if (newQuantity < 1) return;

    setOrderItems(prevItems => prevItems.map(item => {
      if (item.ItemID === itemId) {
        return {
          ...item,
          quantity: newQuantity,
          totalPrice: item.Price * newQuantity
        };
      }
      return item;
    }));
  };

  const handleDeleteItem = (itemId) => {
    setNotification({
      show: true,
      itemId: itemId,
      message: 'Are you sure you want to remove this item from the order?'
    });
  };

  const confirmDeleteItem = (itemId) => {
    setOrderItems(prevItems => prevItems.filter(item => item.ItemID !== itemId));
    setNotification({ show: false, itemId: null, message: '' });
  };

  const saveChanges = async () => {
    setSaveStatus({ saving: true, success: false, error: false });
    try {
      // If no items left, delete the entire order
      if (orderItems.length === 0) {
        await api.delete(`/api/v1/orders/${orderId}`);
        setSaveStatus({ saving: false, success: true, error: false });
        setTimeout(() => navigate('/orders', { state: { refreshOrders: true } }), 1500);
        return;
      }

      const updatedOrder = {
        OrderID: order.OrderID,
        SaleDate: order.SaleDate,
        items: orderItems.map(item => ({
          ItemID: item.ItemID,
          ISBN: item.ISBN,
          Quantity: item.quantity
        }))
      };

      const response = await api.put(`/api/v1/orders/${orderId}`, updatedOrder);

      if (!response.data || response.data.error) {
        throw new Error(response.data?.message || 'Unknown error');
      }

      setSaveStatus({ saving: false, success: true, error: false });
      setTimeout(() => navigate('/orders', { state: { refreshOrders: true } }), 1500);
    } catch (err) {
      setSaveStatus({ saving: false, success: false, error: true });
      setError(`Failed to save: ${err.response?.data?.message || 'Admin privileges required'}`);
    }
  };

  const handleBack = () => {
    navigate('/orders');
  };

  // Function to render the item removal confirmation dialog
  const renderConfirmationDialog = () => {
    if (!notification.show) return null;
    
    // Find the item being deleted to show its details in the confirmation
    const itemToDelete = orderItems.find(item => item.ItemID === notification.itemId);
    const itemTitle = itemToDelete?.Book?.Title || 'this item';
    
    return (
      <div className="fixed top-1/2 left-0 right-0 z-50 flex justify-center transform -translate-y-1/2">
        <div 
          className="bg-gray-100 p-8 rounded-lg shadow-xl border-2 border-gray-400 max-w-md w-full mx-4"
          style={{ backgroundColor: '#f3f4f6' }}
        >
          <h3 className="text-xl font-bold mb-4 text-gray-800 border-b-2 pb-2 border-gray-300">Confirm Item Removal</h3>
          <p className="mb-6 text-gray-700">Are you sure you want to remove "{itemTitle}" from the order?</p>
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setNotification({ show: false, itemId: null, message: '' })}
              className="px-5 py-2 bg-gray-300 text-gray-800 font-medium rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              onClick={() => confirmDeleteItem(notification.itemId)}
              className="px-5 py-2 bg-red-600 text-white font-medium rounded-md hover:bg-red-700"
            >
              Remove Item
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 relative">
      <div className="flex items-center mb-6">
        <button 
          onClick={handleBack}
          className="flex items-center px-4 py-2 mr-4 bg-gray-200 hover:bg-gray-300 rounded"
        >
          <span className="mr-1">←</span> Back to Orders
        </button>
        <h1 className="text-2xl font-semibold">Order Details - {orderId}</h1>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {saveStatus.success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          Changes saved successfully! Redirecting...
        </div>
      )}
      
      {loading ? (
        <div className="text-center py-4">Loading order details...</div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-6">
            <p className="text-gray-700">
              <span className="font-medium">Order Date:</span> {order?.SaleDate && new Date(order.SaleDate).toLocaleDateString()}
            </p>
          </div>
          
          <div className="mb-4">
            <h2 className="text-xl font-medium mb-4">Items</h2>
            {orderItems.length === 0 ? (
              <p className="text-gray-500">No items in this order. The order will be deleted upon saving.</p>
            ) : (
              orderItems.map(item => (
                <div key={item.ItemID} className="border rounded-lg p-4 mb-4 bg-gray-50">
                  <div className="mb-2">
                    <div className="flex justify-between">
                      <p className="font-semibold text-lg">{item.Book?.Title || 'Unknown Book'}</p>
                      <button 
                        onClick={() => handleDeleteItem(item.ItemID)} 
                        className="text-red-500 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </div>
                    <p className="text-gray-600 text-sm">Author: {item.Book?.Author?.FullName || 'Unknown Author'}</p>
                  </div>
                  
                  <div className="mt-3">
                    <p className="font-medium">Quantity:</p>
                    <div className="flex items-center mt-1">
                      <button 
                        onClick={() => handleQuantityChange(item.ItemID, item.quantity - 1)}
                        className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-l"
                      >
                        -
                      </button>
                      <span className="px-4 py-1 bg-white border-t border-b">
                        {item.quantity}
                      </span>
                      <button 
                        onClick={() => handleQuantityChange(item.ItemID, item.quantity + 1)}
                        className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-r"
                      >
                        +
                      </button>
                    </div>
                  </div>
                  
                  <div className="mt-3">
                    <p className="font-medium">Price:</p>
                    <p className="text-lg">${item.totalPrice.toFixed(2)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
          
          <div className="border-t pt-4 mt-6">
            <div className="flex justify-between items-center mb-6">
              <p className="text-xl font-semibold">Total Order Price:</p>
              <p className="text-xl font-bold">${calculateOrderTotal().toFixed(2)}</p>
            </div>
            
            <div className="flex justify-end">
              <button 
                onClick={handleBack}
                className="px-4 py-2 mr-2 border border-gray-300 rounded hover:bg-gray-100"
              >
                Cancel
              </button>
              <button 
                onClick={saveChanges}
                disabled={saveStatus.saving}
                className={`px-4 py-2 bg-blue-500 text-white rounded ${
                  saveStatus.saving ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'
                }`}
              >
                {saveStatus.saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Render modal overlay and confirmation dialog */}
      {notification.show && (
        <>
          {/* Dark overlay covering the entire screen */}
          <div className="fixed inset-0 bg-black bg-opacity-80 z-40"></div>
          {/* The confirmation dialog itself */}
          {renderConfirmationDialog()}
        </>
      )}
    </div>
  );
};

export default OrderDetailPage;