import { api } from './api.js';

export const mlApi = {
  /**
   * Get congestion prediction for a slot.
   * @param {Object} params - Prediction parameters
   * @param {string} params.centreId - Procurement centre ID
   * @param {string} params.slotDate - Slot date in YYYY-MM-DD format
   * @param {number} params.slotHour - Slot hour (e.g. 9, 10, 14)
   * @param {string} params.crop - Crop type
   * @param {number} params.slotCapacity - Maximum farmers for slot
   * @param {number} params.currentBookings - Current booking count
   * @returns {Promise<Object>} Prediction response
   */
  getSlotPrediction: ({ centreId, slotDate, slotHour, crop, slotCapacity, currentBookings }) => {
    const params = new URLSearchParams({
      centre_id: centreId,
      slot_date: slotDate,
      slot_hour: slotHour.toString(),
      crop: crop || 'Unknown',
      slot_capacity: (slotCapacity || 10).toString(),
      current_bookings: (currentBookings || 0).toString(),
    });
    return api.get(`/ml/slot-prediction?${params.toString()}`);
  },

  /**
   * Get model information (for debugging/SIH presentation).
   * @returns {Promise<Object>} Model info
   */
  getModelInfo: () => api.get('/ml/model-info'),
};
