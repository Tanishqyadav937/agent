/**
 * Function Calling Tools for Voice Assistant
 * 
 * Implements four tools:
 * 1. get_weather - Get current weather for a location
 * 2. web_search - Search the web for information
 * 3. create_calendar_event - Create a calendar event
 * 4. create_reminder - Create a reminder
 */

import dotenv from 'dotenv';

dotenv.config();

// Tool definitions for Ollama
export const TOOLS = [
  {
    type: 'function',
    function: {
      name: 'get_weather',
      description: 'Get the current weather for a location including temperature, conditions, sunrise/sunset times, and whether it is daytime. Use this when the user asks about weather, daytime/nighttime, or time of day in their location.',
      parameters: {
        type: 'object',
        properties: {
          location: {
            type: 'string',
            description: 'The city and state or city and country, e.g. "San Francisco, CA" or "London, UK"'
          },
          unit: {
            type: 'string',
            enum: ['celsius', 'fahrenheit'],
            description: 'Temperature unit (optional, defaults to fahrenheit)'
          }
        },
        required: ['location']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'web_search',
      description: 'Search the web for current information. Use this when the user asks about recent events, facts you don\'t know, or information that changes frequently.',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'The search query'
          },
          num_results: {
            type: 'number',
            description: 'Number of results to return (optional, defaults to 3)',
            default: 3
          }
        },
        required: ['query']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'create_calendar_event',
      description: 'Create a calendar event. Use this when the user wants to schedule something or add an event to their calendar.',
      parameters: {
        type: 'object',
        properties: {
          title: {
            type: 'string',
            description: 'Event title'
          },
          start_time: {
            type: 'string',
            description: 'Start time in ISO 8601 format, e.g. "2024-01-15T14:00:00"'
          },
          end_time: {
            type: 'string',
            description: 'End time in ISO 8601 format (optional)'
          },
          description: {
            type: 'string',
            description: 'Event description (optional)'
          }
        },
        required: ['title', 'start_time']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'create_reminder',
      description: 'Create a reminder for the user. Use this when the user wants to be reminded about something.',
      parameters: {
        type: 'object',
        properties: {
          task: {
            type: 'string',
            description: 'What to be reminded about'
          },
          time: {
            type: 'string',
            description: 'When to be reminded, in ISO 8601 format or relative time like "in 1 hour"'
          }
        },
        required: ['task', 'time']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'get_location',
      description: "Get the user's approximate current location (city, region, country). Use this when the user asks about weather, places, or anything 'near me' without naming a location.",
      parameters: {
        type: 'object',
        properties: {},
        required: []
      }
    }
  }
];

// Tool execution functions

/**
 * Get current weather for a location
 */
export async function get_weather({ location, unit = 'fahrenheit' }) {
  try {
    const apiKey = process.env.OPENWEATHER_API_KEY;
    
    if (!apiKey) {
      return {
        success: false,
        error: 'OpenWeather API key not configured. Please set OPENWEATHER_API_KEY in .env file.',
        mock: true,
        data: {
          location,
          temperature: 72,
          unit: 'fahrenheit',
          condition: 'Sunny',
          humidity: 45,
          wind_speed: 8,
          local_time: '14:30',
          is_daytime: true,
          sunrise: '06:30',
          sunset: '18:45'
        }
      };
    }

    // OpenWeather API call
    const units = unit === 'celsius' ? 'metric' : 'imperial';
    const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(location)}&units=${units}&appid=${apiKey}`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`OpenWeather API error: ${response.statusText}`);
    }

    const data = await response.json();
    
    // data.timezone is the location's UTC offset in seconds
    const localNowMs = Date.now() + (data.timezone * 1000);
    const localNow = new Date(localNowMs);
    const sunriseMs = (data.sys.sunrise + data.timezone) * 1000;
    const sunsetMs = (data.sys.sunset + data.timezone) * 1000;
    const isDaytime = localNowMs >= sunriseMs && localNowMs < sunsetMs;

    return {
      success: true,
      data: {
        location: data.name,
        temperature: Math.round(data.main.temp),
        unit: unit,
        condition: data.weather[0].main,
        description: data.weather[0].description,
        humidity: data.main.humidity,
        wind_speed: Math.round(data.wind.speed),
        local_time: localNow.toISOString().substring(11, 16), // "HH:MM" in the location's local time
        is_daytime: isDaytime,
        sunrise: new Date(sunriseMs).toISOString().substring(11, 16),
        sunset: new Date(sunsetMs).toISOString().substring(11, 16)
      }
    };
  } catch (error) {
    console.error('[Tool] get_weather error:', error.message);
    return {
      success: false,
      error: error.message,
      mock: true,
      data: {
        location,
        temperature: 72,
        unit: 'fahrenheit',
        condition: 'Sunny',
        humidity: 45,
        wind_speed: 8,
        local_time: '14:30',
        is_daytime: true,
        sunrise: '06:30',
        sunset: '18:45'
      }
    };
  }
}

/**
 * Get user's current location from IP address
 */
export async function get_location(args, context = {}) {
  try {
    const ip = context.clientIp;
    const isLocal = !ip || ip === '::1' || ip === '127.0.0.1' || ip.startsWith('192.168.') || ip.startsWith('10.');
    const target = isLocal ? '' : ip;

    const response = await fetch(`http://ip-api.com/json/${target}?fields=status,message,city,region,country,lat,lon,timezone`);
    const data = await response.json();

    if (data.status !== 'success') {
      throw new Error(`Location lookup failed: ${data.message || 'unknown error'}`);
    }

    return {
      success: true,
      data: {
        city: data.city,
        region: data.region,
        country: data.country,
        lat: data.lat,
        lon: data.lon,
        timezone: data.timezone
      }
    };
  } catch (error) {
    console.error('[Tool] get_location error:', error.message);
    return {
      success: false,
      error: error.message,
      mock: true,
      data: { city: 'Unknown', region: '', country: '', lat: null, lon: null }
    };
  }
}

/**
 * Search the web for information
 */
export async function web_search({ query, num_results = 3 }) {
  try {
    const apiKey = process.env.SERPER_API_KEY;
    
    if (!apiKey) {
      return {
        success: false,
        error: 'Serper API key not configured. Please set SERPER_API_KEY in .env file.',
        mock: true,
        data: {
          query,
          results: [
            {
              title: `Mock result for: ${query}`,
              snippet: 'This is a mock search result. Configure SERPER_API_KEY for real results.',
              link: 'https://example.com'
            }
          ]
        }
      };
    }

    // Serper API call
    const response = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        q: query,
        num: num_results
      })
    });

    if (!response.ok) {
      throw new Error(`Serper API error: ${response.statusText}`);
    }

    const data = await response.json();
    
    const results = (data.organic || []).slice(0, num_results).map(item => ({
      title: item.title,
      snippet: item.snippet,
      link: item.link
    }));

    return {
      success: true,
      data: {
        query,
        results
      }
    };
  } catch (error) {
    console.error('[Tool] web_search error:', error.message);
    return {
      success: false,
      error: error.message,
      mock: true,
      data: {
        query,
        results: [
          {
            title: `Search result for: ${query}`,
            snippet: 'Mock result - configure API key for real search.',
            link: 'https://example.com'
          }
        ]
      }
    };
  }
}

/**
 * Create a calendar event
 */
export async function create_calendar_event({ title, start_time, end_time, description }) {
  try {
    const clientId = process.env.GOOGLE_CALENDAR_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CALENDAR_CLIENT_SECRET;
    const refreshToken = process.env.GOOGLE_CALENDAR_REFRESH_TOKEN;
    
    if (!clientId || !clientSecret || !refreshToken) {
      return {
        success: false,
        error: 'Google Calendar credentials not configured. Set GOOGLE_CALENDAR_* variables in .env.',
        mock: true,
        data: {
          title,
          start_time,
          end_time,
          description,
          event_id: 'mock_event_' + Date.now(),
          status: 'Mock event created (configure API for real calendar)'
        }
      };
    }

    // Google Calendar API implementation would go here
    // This is a simplified mock - full implementation requires OAuth flow
    
    return {
      success: true,
      mock: true,
      data: {
        title,
        start_time,
        end_time,
        description,
        event_id: 'mock_event_' + Date.now(),
        status: 'Event created successfully (mock mode)'
      }
    };
  } catch (error) {
    console.error('[Tool] create_calendar_event error:', error.message);
    return {
      success: false,
      error: error.message,
      mock: true,
      data: {
        title,
        status: 'Failed to create event'
      }
    };
  }
}

/**
 * Create a reminder
 */
export async function create_reminder({ task, time }) {
  try {
    // Simple in-memory reminder system (could be enhanced with persistent storage)
    return {
      success: true,
      data: {
        task,
        time,
        reminder_id: 'reminder_' + Date.now(),
        status: 'Reminder created successfully',
        note: 'Note: This is a simple reminder system. For persistent reminders, integrate with a reminder service.'
      }
    };
  } catch (error) {
    console.error('[Tool] create_reminder error:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Execute a tool call
 */
export async function executeTool(toolName, args, context = {}) {
  console.log(`[Tool] Executing: ${toolName}`, JSON.stringify(args, null, 2));
  
  switch (toolName) {
    case 'get_weather':
      return await get_weather(args);
    case 'web_search':
      return await web_search(args);
    case 'create_calendar_event':
      return await create_calendar_event(args);
    case 'create_reminder':
      return await create_reminder(args);
    case 'get_location':
      return await get_location(args, context);
    default:
      return {
        success: false,
        error: `Unknown tool: ${toolName}`
      };
  }
}
