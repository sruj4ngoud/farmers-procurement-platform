"""MSP (Minimum Support Price) configuration for government procurement.

These are approximate MSP values for reference. The actual procurement price
is determined by the government and may vary.
"""

MSP_DATA = {
    # Cereals
    "Paddy": 2320,
    "Wheat": 2350,
    "Maize": 2090,
    "Barley": 1850,
    "Sorghum (Jowar)": 3180,
    "Pearl Millet (Bajra)": 2500,
    "Finger Millet (Ragi)": 3880,
    "Foxtail Millet": 3500,
    "Little Millet": 3500,
    "Kodo Millet": 3500,
    "Barnyard Millet": 3500,
    "Proso Millet": 3500,
    "Browntop Millet": 3500,
    "Oat": 2200,
    "Buckwheat": 3000,

    # Pulses
    "Red Gram (Tur/Arhar)": 7300,
    "Black Gram (Urad)": 7400,
    "Green Gram (Moong)": 8550,
    "Bengal Gram (Chickpea/Chana)": 5450,
    "Lentil (Masoor)": 6500,
    "Field Pea": 5200,
    "Cowpea (Lobia)": 5000,
    "Horse Gram": 4500,
    "Moth Bean": 5000,

    # Oilseeds
    "Soybean": 4892,
    "Groundnut": 6540,
    "Sunflower": 6760,
    "Sesame": 7800,
    "Mustard": 5650,
    "Safflower": 6200,
    "Castor": 6540,
    "Linseed": 5800,
    "Niger Seed": 7300,

    # Cash Crops
    "Cotton": 7121,
    "Sugarcane": 3150,
    "Tobacco": 2550,

    # Fiber Crops
    "Jute": 4800,
    "Mesta": 4500,

    # Plantation
    "Tea": 2500,
    "Coffee": 3000,
    "Coconut": 2500,
    "Arecanut": 3000,
    "Rubber": 1800,

    # Spices
    "Pepper": 6500,
    "Cardamom": 32000,
    "Turmeric": 12500,
    "Cumin": 6000,
    "Coriander": 5500,
    "Chilli": 14000,
    "Fenugreek": 5500,
    "Ginger": 6000,
    "Garlic": 5000,
    "Tamarind": 4000,

    # Vegetables
    "Potato": 2000,
    "Tomato": 2500,
    "Onion": 1800,
    "Brinjal (Eggplant)": 2000,
    "Okra (Lady's Finger)": 2500,
    "Cabbage": 1500,
    "Cauliflower": 2000,
    "Carrot": 2000,
    "Radish": 1500,
    "Beetroot": 2000,
    "Bottle Gourd": 1500,
    "Bitter Gourd": 2500,
    "Ridge Gourd": 2000,
    "Pumpkin": 1500,
    "Cucumber": 1500,
    "Green Peas": 3500,
    "French Bean": 3000,
    "Drumstick": 3000,
    "Sweet Potato": 2000,

    # Tubers
    "Tapioca (Cassava)": 1500,

    # Fruits
    "Banana": 2000,
    "Mango": 2500,
    "Guava": 1500,
    "Papaya": 2000,
    "Pomegranate": 3000,
    "Grapes": 2500,
    "Orange": 2500,
    "Sweet Lime (Mosambi)": 2000,
    "Lemon": 2500,
    "Watermelon": 1500,
    "Muskmelon": 1500,
    "Pineapple": 2000,
    "Apple": 3000,
    "Sapota (Chikoo)": 2000,
    "Jackfruit": 2000,
    "Custard Apple": 2500,
}


def get_msp(crop_name: str) -> int | None:
    """Get MSP for a crop. Returns None if not found."""
    return MSP_DATA.get(crop_name)


def get_all_msp() -> dict[str, int]:
    """Get all MSP data."""
    return MSP_DATA.copy()
