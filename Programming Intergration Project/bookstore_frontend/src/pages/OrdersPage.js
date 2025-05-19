import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const OrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState('order'); // 'order', 'book', 'author'
  const [currentPage, setCurrentPage] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [filterDate, setFilterDate] = useState('');
  const [showCalendar, setShowCalendar] = useState(false);
  const [dateFilterType, setDateFilterType] = useState('single'); // 'single', 'range'
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  // Active date filter
  const [activeDateFilter, setActiveDateFilter] = useState({
    type: 'none',
    singleDate: '',
    startDate: '',
    endDate: ''
  });
  
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Check authentication before loading orders
  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/login');
    }
  }, [user, authLoading, navigate]);

  // Fetch orders when component mounts or filters/pagination changes
  useEffect(() => {
    if (user) {
      // Check if we need to refresh orders (coming back from OrderDetailPage after changes)
      const shouldRefresh = location.state?.refreshOrders;
      if (shouldRefresh) {
        // Clear refresh flag to prevent continuous refreshing
        navigate(location.pathname, { replace: true, state: {} });
      }
      fetchOrders();
    }
  }, [user, location.state, currentPage, perPage, searchTerm, searchType, activeDateFilter]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      // Build query parameters based on filters
      const params = new URLSearchParams();
      
      // Add pagination parameters - use server-side pagination
      params.append('page', currentPage);
      params.append('per_page', perPage);
      
      // Add search term based on search type
      if (searchTerm.trim()) {
        if (searchType === 'order') {
          params.append('search', searchTerm);
        } else if (searchType === 'book') {
          params.append('book_title', searchTerm);
        } else if (searchType === 'author') {
          params.append('author_last_name', searchTerm);
        }
      }
      
      // Add date filters
      if (activeDateFilter.type === 'single' && activeDateFilter.singleDate) {
        // For single date, use the same date for both start and end
        params.append('start_date', activeDateFilter.singleDate);
        params.append('end_date', activeDateFilter.singleDate);
      } else if (activeDateFilter.type === 'range' && activeDateFilter.startDate && activeDateFilter.endDate) {
        params.append('start_date', activeDateFilter.startDate);
        params.append('end_date', activeDateFilter.endDate);
      }
      
      // Use the optimized search endpoint with server-side filtering and pagination
      const response = await api.get('/api/v1/orders/search', { params });
      
      // Process the orders to calculate total price
      const processedOrders = (response.data.orders || []).map(order => {
        const orderDetails = Array.isArray(order.OrderDetails) ? order.OrderDetails : [];
        
        const totalPrice = orderDetails.reduce((sum, detail) => {
          const price = detail.Price || 0;
          const quantity = detail.Quantity || 1;
          return sum + (price * quantity);
        }, 0);
        
        return {
          ...order,
          calculatedTotalPrice: totalPrice
        };
      });
      
      // Use pagination data from the server response
      setOrders(processedOrders);
      setTotalOrders(response.data.count || 0);
      setTotalPages(response.data.total_pages || 1);
      // In case the server returns a different per_page value
      if (response.data.per_page) {
        setPerPage(response.data.per_page);
      }
      
    } catch (err) {
      console.error('Error fetching orders:', err);
      
      if (err.response) {
        if (err.response.status === 401) {
          setError('Your session has expired. Please log in again.');
          setTimeout(() => navigate('/login'), 2000);
        } else if (err.response.status === 422) {
          const errorMsg = err.response.data?.message || '';
          if (errorMsg.includes('Invalid date format')) {
            setError('Invalid date format. Please select another date or clear the filter.');
          } else {
            setError(`Validation error: ${errorMsg}`);
          }
        } else {
          setError(`Failed to fetch orders: ${err.response.data.message || err.message}`);
        }
      } else {
        setError('Network error. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page when searching
    // The fetchOrders will be triggered by the useEffect
  };

  const handleSearchTypeChange = (type) => {
    setSearchType(type);
    setCurrentPage(1); // Reset to first page when changing search type
    // The fetchOrders will be triggered by the useEffect
  };

  const handleDateSelect = (e) => {
    setFilterDate(e.target.value);
  };

  const handleStartDateSelect = (e) => {
    setStartDate(e.target.value);
  };

  const handleEndDateSelect = (e) => {
    setEndDate(e.target.value);
  };

  const handleFilterTypeChange = (type) => {
    setDateFilterType(type);
    
    if (type === 'single') {
      setStartDate('');
      setEndDate('');
      setFilterDate(filterDate || '');
    } else if (type === 'range') {
      setFilterDate('');
    } else if (type === 'none' || !type) {
      setFilterDate('');
      setStartDate('');
      setEndDate('');
    }
  };

  const handlePerPageChange = (newPerPage) => {
    setPerPage(newPerPage);
    setCurrentPage(1); // Reset to first page when changing items per page
  };

  const applyDateFilter = () => {
    if (dateFilterType === 'single') {
      setActiveDateFilter({
        type: 'single',
        singleDate: filterDate,
        startDate: '',
        endDate: ''
      });
    } else if (dateFilterType === 'range') {
      setActiveDateFilter({
        type: 'range',
        singleDate: '',
        startDate: startDate,
        endDate: endDate
      });
    } else {
      setActiveDateFilter({
        type: 'none',
        singleDate: '',
        startDate: '',
        endDate: ''
      });
    }
    
    setCurrentPage(1); // Reset to first page when applying date filter
    setShowCalendar(false);
    // fetchOrders will be triggered by the useEffect
  };

  const clearAllFilters = () => {
    setSearchTerm('');
    setSearchType('order');
    setFilterDate('');
    setStartDate('');
    setEndDate('');
    setActiveDateFilter({
      type: 'none',
      singleDate: '',
      startDate: '',
      endDate: ''
    });
    setCurrentPage(1); // Reset to first page when clearing filters
    // fetchOrders will be triggered by the useEffect
  };

  const generatePaginationNumbers = () => {
    const pages = [];
    
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
      return pages;
    }
    
    const maxPagesToShow = 5;
    
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
    
    if (endPage - startPage + 1 < maxPagesToShow && startPage > 1) {
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  const getSearchTypeLabel = () => {
    switch (searchType) {
      case 'book': return 'Book Title';
      case 'author': return 'Author Name';
      default: return 'Order ID';
    }
  };

  const getDateFilterDisplay = () => {
    if (activeDateFilter.type === 'single' && activeDateFilter.singleDate) {
      return new Date(activeDateFilter.singleDate).toLocaleDateString();
    } else if (activeDateFilter.type === 'range' && activeDateFilter.startDate && activeDateFilter.endDate) {
      return `${new Date(activeDateFilter.startDate).toLocaleDateString()} - ${new Date(activeDateFilter.endDate).toLocaleDateString()}`;
    } else {
      return 'All Dates';
    }
  };

  // Calculate the range of items being shown
  const calculateItemsRange = () => {
    const startItem = totalOrders === 0 ? 0 : (currentPage - 1) * perPage + 1;
    const endItem = Math.min(startItem + perPage - 1, totalOrders);
    
    return {
      startItem,
      endItem,
      totalItems: totalOrders
    };
  };

  if (authLoading) {
    return <div className="text-center py-4">Checking authentication...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Orders</h1>
      
      <div className="bg-white rounded-lg shadow p-6">
        {/* Search and filter */}
        <div className="flex mb-4">
          <div className="flex-1 mr-2">
            <div className="flex">
              {/* Search Type Dropdown */}
              <div className="relative mr-2">
                <button
                  type="button"
                  className="w-40 text-left py-2 pl-3 pr-10 border border-gray-300 rounded-md"
                  onClick={() => document.getElementById('search-type-dropdown').classList.toggle('hidden')}
                >
                  {getSearchTypeLabel()}
                </button>
                <div id="search-type-dropdown" className="absolute z-50 mt-1 w-40 bg-white rounded-md shadow-lg border border-gray-200 hidden">
                  <div className="py-1">
                    <button
                      className={`block w-full text-left px-4 py-2 text-sm ${searchType === 'order' ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                      onClick={() => {
                        handleSearchTypeChange('order');
                        document.getElementById('search-type-dropdown').classList.add('hidden');
                      }}
                    >
                      Order ID
                    </button>
                    <button
                      className={`block w-full text-left px-4 py-2 text-sm ${searchType === 'book' ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                      onClick={() => {
                        handleSearchTypeChange('book');
                        document.getElementById('search-type-dropdown').classList.add('hidden');
                      }}
                    >
                      Book Title
                    </button>
                    <button
                      className={`block w-full text-left px-4 py-2 text-sm ${searchType === 'author' ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                      onClick={() => {
                        handleSearchTypeChange('author');
                        document.getElementById('search-type-dropdown').classList.add('hidden');
                      }}
                    >
                      Author Name
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Search Input */}
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder={`Search by ${getSearchTypeLabel()}`}
                  className="w-full pl-3 pr-10 py-2 border border-gray-300 rounded-md"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch(e);
                    }
                  }}
                />
              </div>
            </div>
          </div>
          
          {/* Date Filter */}
          <div className="flex-1 relative">
            <button
              className="w-full text-left py-2 pl-3 pr-10 border border-gray-300 rounded-md"
              onClick={() => setShowCalendar(!showCalendar)}
            >
              <span>{getDateFilterDisplay()}</span>
            </button>
            
            {/* Calendar Dropdown with increased z-index */}
            {showCalendar && (
              <div className="absolute z-50 mt-1 w-full bg-gray-100 rounded-md border-2 border-gray-500" style={{ backgroundColor: '#f3f4f6' }}>
              <div className="p-4" style={{ backgroundColor: '#f3f4f6' }}>
                  {/* Filter Type Selection */}
                  <div className="mb-3">
                    <div className="flex mb-2">
                      <button
                        className={`flex-1 px-3 py-1 text-sm ${dateFilterType === 'single' ? 'bg-blue-100 border border-blue-300' : ''}`}
                        onClick={() => handleFilterTypeChange('single')}
                      >
                        Single Date
                      </button>
                      <button
                        className={`flex-1 px-3 py-1 text-sm ${dateFilterType === 'range' ? 'bg-blue-100 border border-blue-300' : ''}`}
                        onClick={() => handleFilterTypeChange('range')}
                      >
                        Date Range
                      </button>
                      <button
                        className={`flex-1 px-3 py-1 text-sm ${!dateFilterType || (dateFilterType === 'none') ? 'bg-blue-100 border border-blue-300' : ''}`}
                        onClick={() => handleFilterTypeChange('none')}
                      >
                        All Dates
                      </button>
                    </div>
                  </div>
                  
                  {/* Date Selector */}
                  {dateFilterType === 'single' ? (
                    <div className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Select Date</label>
                      <input
                        type="date"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={filterDate}
                        onChange={handleDateSelect}
                      />
                    </div>
                  ) : dateFilterType === 'range' ? (
                    <div className="mb-3">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                          <input
                            type="date"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            value={startDate}
                            onChange={handleStartDateSelect}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                          <input
                            type="date"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            value={endDate}
                            onChange={handleEndDateSelect}
                          />
                        </div>
                      </div>
                    </div>
                  ) : null}
                  
                  {/* Apply and Clear Buttons */}
                  <div className="flex justify-between">
                    <button
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                      onClick={applyDateFilter}
                    >
                      Apply Filter
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Active filters display */}
        {(activeDateFilter.type !== 'none' || searchTerm.trim()) && (
          <div className="flex flex-wrap items-center mb-4 text-sm">
            <span className="mr-2 font-medium">Active Filters:</span>
            {searchTerm.trim() && (
              <span className="mr-2 mb-1 bg-gray-100 px-2 py-1 rounded">
                {getSearchTypeLabel()}: {searchTerm}
                <button 
                  className="ml-1 text-gray-500 hover:text-gray-700"
                  onClick={() => setSearchTerm('')}
                >
                  ×
                </button>
              </span>
            )}
            {activeDateFilter.type === 'single' && activeDateFilter.singleDate && (
              <span className="mr-2 mb-1 bg-gray-100 px-2 py-1 rounded">
                Date: {new Date(activeDateFilter.singleDate).toLocaleDateString()}
                <button 
                  className="ml-1 text-gray-500 hover:text-gray-700"
                  onClick={() => setActiveDateFilter({...activeDateFilter, type: 'none', singleDate: ''})}
                >
                  ×
                </button>
              </span>
            )}
            {activeDateFilter.type === 'range' && activeDateFilter.startDate && activeDateFilter.endDate && (
              <span className="mr-2 mb-1 bg-gray-100 px-2 py-1 rounded">
                Date Range: {new Date(activeDateFilter.startDate).toLocaleDateString()} - {new Date(activeDateFilter.endDate).toLocaleDateString()}
                <button 
                  className="ml-1 text-gray-500 hover:text-gray-700"
                  onClick={() => setActiveDateFilter({...activeDateFilter, type: 'none', startDate: '', endDate: ''})}
                >
                  ×
                </button>
              </span>
            )}
            {(activeDateFilter.type !== 'none' || searchTerm.trim()) && (
              <button 
                className="ml-2 text-blue-500 hover:text-blue-700"
                onClick={clearAllFilters}
              >
                Clear All
              </button>
            )}
          </div>
        )}
        
        {/* Error message display */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <span>{error}</span>
            <button 
              className="float-right"
              onClick={() => setError('')}
            >
              &times;
            </button>
          </div>
        )}
        
        {/* Items Per Page Selector */}
        <div className="flex justify-end mb-2">
          <div className="relative inline-block text-left">
            <button
              type="button"
              className="inline-flex justify-center w-32 rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
              onClick={() => document.getElementById('per-page-menu').classList.toggle('hidden')}
            >
              {perPage} per page
            </button>
            <div
              id="per-page-menu"
              className="hidden origin-top-right absolute right-0 mt-2 w-32 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50"
            >
              <div className="py-1">
                {[5, 10, 25, 50, 100].map(option => (
                  <button
                    key={option}
                    className={`block w-full text-left px-4 py-2 text-sm ${perPage === option ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                    onClick={() => {
                      handlePerPageChange(option);
                      document.getElementById('per-page-menu').classList.add('hidden');
                    }}
                  >
                    {option} per page
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Table */}
        {loading ? (
          <div className="text-center py-4">Loading orders...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Items
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders.length > 0 ? (
                  orders.map((order) => (
                    <tr key={order.OrderID}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {order.OrderID}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {/* Display total quantity of items */}
                        {Array.isArray(order.OrderDetails) ? 
                          order.OrderDetails.reduce((total, item) => total + (item.Quantity || 1), 0) : 
                          order.OrderDetails?.length || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {order.SaleDate && new Date(order.SaleDate).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {/* Use the pre-calculated total price that accounts for quantity */}
                        ${order.calculatedTotalPrice ? 
                          order.calculatedTotalPrice.toFixed(2) : 
                          (Array.isArray(order.OrderDetails) ? 
                            order.OrderDetails.reduce((sum, detail) => 
                              sum + ((detail.Price || 0) * (detail.Quantity || 1)), 0) : 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <Link to={`/orders/${order.OrderID}`} className="text-blue-500 hover:text-blue-700">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                      No orders found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination */}
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-gray-500">
            {(() => {
              const { startItem, endItem, totalItems } = calculateItemsRange();
              return totalItems > 0 
                ? `Showing ${startItem} to ${endItem} of ${totalItems} results` 
                : 'No results found';
            })()}
          </div>
          <div className="flex space-x-1">
            {/* Previous Button */}
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className={`px-3 py-1 border ${currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-600 hover:bg-gray-50'} rounded`}
            >
              &lt;
            </button>
            
            {/* Page Buttons Logic */}
            {totalPages <= 7 ? (
              // Show all pages if 7 or fewer
              [...Array(totalPages)].map((_, index) => (
                <button
                  key={index + 1}
                  onClick={() => setCurrentPage(index + 1)}
                  className={`px-3 py-1 border rounded ${currentPage === (index + 1) ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                >
                  {index + 1}
                </button>
              ))
            ) : (
              // Show pagination with ellipsis for more than 7 pages
              <>
                {currentPage > 3 && (
                  <>
                    <button
                      onClick={() => setCurrentPage(1)}
                      className={`px-3 py-1 border rounded bg-white text-gray-600 hover:bg-gray-50`}
                    >
                      1
                    </button>
                    {currentPage > 4 && (
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 5))}
                        title="Jump 5 pages back"
                        className="px-3 py-1 border rounded bg-white text-gray-600 hover:bg-gray-50"
                      >
                        ...
                      </button>
                    )}
                  </>
                )}
                
                {generatePaginationNumbers().map(pageNum => (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1 border rounded ${currentPage === pageNum ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                  >
                    {pageNum}
                  </button>
                ))}
                
                {currentPage < totalPages - 2 && (
                  <>
                    {currentPage < totalPages - 3 && (
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 5))}
                        title="Jump 5 pages forward"
                        className="px-3 py-1 border rounded bg-white text-gray-600 hover:bg-gray-50"
                      >
                        ...
                      </button>
                    )}
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      className={`px-3 py-1 border rounded bg-white text-gray-600 hover:bg-gray-50`}
                    >
                      {totalPages}
                    </button>
                  </>
                )}
              </>
            )}
            
            {/* Next Button */}
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className={`px-3 py-1 border ${currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-600 hover:bg-gray-50'} rounded`}
            >
              &gt;
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrdersPage;