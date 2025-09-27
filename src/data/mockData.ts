import { Load, ChatMessage } from '@/types/logistics';

export const mockLoads: Load[] = [
  {
    id: 'AUG-2930487',
    origin: 'Seattle, WA',
    destination: 'Meadford, OR',
    status: 'unassigned',
    date: 'Mar 12',
    customer: 'Dawn Foods',
    mode: 'FT',
    equipment: 'Reefer 34°F 53 ft',
    weight: '45,000 lbs',
    commodity: 'Bananas, flour, non-perishables',
    packingType: 'Pallets',
    notes: 'Food grade required. Contact Ben 24/7 with any loading or unloading issues/delay. Please do not leave the shipper/receiver without communication/approval from Ben. In/out times must be accurate.',
    pickupCoords: [47.6062, -122.3321],
    deliveryCoords: [42.3265, -122.8756],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '3842 Corvina St',
        city: 'Seattle',
        state: 'WA',
        zipCode: '98109',
        date: 'Mar 12',
        timeWindow: '9AM - 5PM PT',
        coordinates: [47.6062, -122.3321]
      },
      {
        id: '2',
        type: 'delivery',
        address: '1500 Journey Rd',
        city: 'Meadford',
        state: 'OR',
        zipCode: '97504',
        date: 'Mar 15',
        timeWindow: '9AM - 5PM CT',
        coordinates: [42.3265, -122.8756]
      }
    ]
  },
  {
    id: 'AUG-2930488',
    origin: 'Detroit, MI',
    destination: 'Dallas, TX',
    status: 'assigned',
    date: 'Mar 12',
    customer: 'AutoParts Inc',
    mode: 'FTL',
    equipment: 'Dry Van 53 ft',
    weight: '42,000 lbs',
    commodity: 'Automotive parts',
    packingType: 'Pallets',
    notes: 'Standard dry freight. Notify dispatch of any delays.',
    pickupCoords: [42.3314, -83.0458],
    deliveryCoords: [32.7767, -96.7970],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '1234 Industrial Dr',
        city: 'Detroit',
        state: 'MI',
        zipCode: '48201',
        date: 'Mar 13',
        timeWindow: '8AM - 4PM ET',
        coordinates: [42.3314, -83.0458]
      },
      {
        id: '2',
        type: 'delivery',
        address: '5678 Commerce St',
        city: 'Dallas',
        state: 'TX',
        zipCode: '75201',
        date: 'Mar 16',
        timeWindow: '9AM - 5PM CT',
        coordinates: [32.7767, -96.7970]
      }
    ]
  },
  {
    id: 'AUG-2930489',
    origin: 'San Francisco, CA',
    destination: 'Houston, TX',
    status: 'in-transit',
    date: 'Mar 12',
    badges: ['T&T'],
    customer: 'TechCorp',
    mode: 'FTL',
    equipment: 'Dry Van 53 ft',
    weight: '38,000 lbs',
    commodity: 'Electronics',
    packingType: 'Crates',
    notes: 'High value cargo. GPS tracking required.',
    pickupCoords: [37.7749, -122.4194],
    deliveryCoords: [29.7604, -95.3698],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '3842 Corvina St',
        city: 'San Francisco',
        state: 'CA',
        zipCode: '73829',
        date: 'Mar 12',
        timeWindow: '9AM - 5PM PT',
        coordinates: [37.7749, -122.4194]
      },
      {
        id: '2',
        type: 'delivery',
        address: '1500 Journey Rd',
        city: 'Houston',
        state: 'TX',
        zipCode: '33607',
        date: 'Mar 15',
        timeWindow: '9AM - 5PM CT',
        coordinates: [29.7604, -95.3698]
      }
    ]
  },
  {
    id: 'AUG-2930490',
    origin: 'Las Vegas, NV',
    destination: 'Las Vegas, NV',
    status: 'dispatched',
    date: 'Mar 12',
    badges: ['Chipotle'],
    customer: 'Food Service Co',
    mode: 'LTL',
    equipment: 'Box Truck',
    weight: '15,000 lbs',
    commodity: 'Restaurant supplies',
    packingType: 'Boxes',
    notes: 'Multiple stops within city. Check with dispatcher for route optimization.',
    pickupCoords: [36.1699, -115.1398],
    deliveryCoords: [36.1699, -115.1398],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '2500 Las Vegas Blvd',
        city: 'Las Vegas',
        state: 'NV',
        zipCode: '89109',
        date: 'Mar 13',
        timeWindow: '6AM - 2PM PT',
        coordinates: [36.1699, -115.1398]
      },
      {
        id: '2',
        type: 'delivery',
        address: '3500 Paradise Rd',
        city: 'Las Vegas',
        state: 'NV',
        zipCode: '89169',
        date: 'Mar 13',
        timeWindow: '10AM - 6PM PT',
        coordinates: [36.1699, -115.1398]
      }
    ]
  },
  {
    id: 'AUG-2930491',
    origin: 'Los Angeles, CA',
    destination: 'Las Vegas, NV',
    status: 'dispatched',
    date: 'Mar 12',
    customer: 'Retail Chain',
    mode: 'FTL',
    equipment: 'Dry Van 48 ft',
    weight: '40,000 lbs',
    commodity: 'General merchandise',
    packingType: 'Mixed',
    notes: 'Weekend delivery required. Notify receiver 24hrs in advance.',
    pickupCoords: [34.0522, -118.2437],
    deliveryCoords: [36.1699, -115.1398],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '1000 Industrial Way',
        city: 'Los Angeles',
        state: 'CA',
        zipCode: '90021',
        date: 'Mar 14',
        timeWindow: '7AM - 3PM PT',
        coordinates: [34.0522, -118.2437]
      },
      {
        id: '2',
        type: 'delivery',
        address: '4000 Vegas Dr',
        city: 'Las Vegas',
        state: 'NV',
        zipCode: '89103',
        date: 'Mar 15',
        timeWindow: '8AM - 4PM PT',
        coordinates: [36.1699, -115.1398]
      }
    ]
  },
  {
    id: 'AUG-2930492',
    origin: 'New York, NY',
    destination: 'Quebec City, QC',
    status: 'at-pickup',
    date: 'Mar 12',
    badges: ['Home Furniture World'],
    customer: 'Furniture Plus',
    mode: 'FTL',
    equipment: 'Moving Van 26 ft',
    weight: '25,000 lbs',
    commodity: 'Household goods',
    packingType: 'Wrapped',
    notes: 'White glove service required. Handle with care.',
    pickupCoords: [40.7128, -74.0060],
    deliveryCoords: [46.8139, -71.2080],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '789 Broadway',
        city: 'New York',
        state: 'NY',
        zipCode: '10003',
        date: 'Mar 12',
        timeWindow: '8AM - 6PM ET',
        coordinates: [40.7128, -74.0060]
      },
      {
        id: '2',
        type: 'delivery',
        address: '123 Rue Saint-Jean',
        city: 'Quebec City',
        state: 'QC',
        zipCode: 'G1R 1S4',
        date: 'Mar 14',
        timeWindow: '9AM - 5PM ET',
        coordinates: [46.8139, -71.2080]
      }
    ]
  },
  {
    id: 'AUG-2930493',
    origin: 'New Orleans, LA',
    destination: 'Dallas, TX',
    status: 'loaded',
    date: 'Mar 12',
    customer: 'Energy Corp',
    mode: 'Flatbed',
    equipment: 'Flatbed 48 ft',
    weight: '48,000 lbs',  
    commodity: 'Steel pipes',
    packingType: 'Secured',
    notes: 'Oversized load. Escort vehicle required for highway travel.',
    pickupCoords: [29.9511, -90.0715],
    deliveryCoords: [32.7767, -96.7970],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: '500 Port St',
        city: 'New Orleans',
        state: 'LA',
        zipCode: '70130',
        date: 'Mar 13',
        timeWindow: '6AM - 2PM CT',
        coordinates: [29.9511, -90.0715]
      },
      {
        id: '2',
        type: 'delivery',
        address: '2000 Industrial Blvd',
        city: 'Dallas',
        state: 'TX',
        zipCode: '75207',
        date: 'Mar 15',
        timeWindow: '8AM - 4PM CT',
        coordinates: [32.7767, -96.7970]
      }
    ]
  }
];

export const mockChatMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'system',
    content: 'Good morning! Augie is working on Track & Trace → track now over the last 30 days.',
    timestamp: 'Mar 11, 9:51 AM'
  },
  {
    id: '2',
    role: 'human',
    content: 'See transcript',
    timestamp: 'Mar 11, 9:51 AM'
  },
  {
    id: '3',
    role: 'human',
    content: 'Great!',
    timestamp: 'Mar 11, 9:51 AM'
  },
  {
    id: '4',
    role: 'agent',
    content: "I've attempted to call Ben twice but couldn't get a hold of him. I'll reach out to the dispatcher. What is their contact info?",
    timestamp: 'Mar 12, 9:00 AM'
  },
  {
    id: '5',
    role: 'human',
    content: '712-293-2037',
    timestamp: 'Mar 11, 9:51 AM'
  },
  {
    id: '6',
    role: 'agent',
    content: "The dispatcher's name is Holly. Call, don't text.",
    timestamp: 'Feb 18, 9:51 AM'
  },
  {
    id: '7',
    role: 'system',
    content: 'Knowledge updated',
    timestamp: 'Feb 18, 9:51 AM'
  },
  {
    id: '8',
    role: 'agent',
    content: 'Calling Holly now...',
    timestamp: 'Feb 18, 9:51 AM'
  },
  {
    id: '9',
    role: 'system',
    content: '',
    timestamp: '',
    attachments: [{
      id: 'call-1',
      type: 'call',
      name: 'Augie <> Holly, dispatcher',
      duration: '0:10',
      participants: ['Augie', 'Holly']
    }]
  }
];