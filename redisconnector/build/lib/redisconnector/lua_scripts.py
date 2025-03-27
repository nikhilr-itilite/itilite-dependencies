update_min_price_transformer_lua_script = """
local key = KEYS[1]
local new_price = tonumber(ARGV[1])
local new_price_tc = tonumber(ARGV[2])

-- Retrieve the current JSON value from the key
local current_data = redis.call('GET', key)

-- Initialize current_price to nil
local current_price = nil

if current_data then
    -- Parse the JSON string
    local data = cjson.decode(current_data)
    current_price = tonumber(data.price)
end

-- Check if current_price exists and compare it with new_price
if not current_price or new_price < current_price then
    -- Create a new table for the updated data
    local updated_data = {
        price = new_price,
        price_tc = new_price_tc
    }

    -- Convert the table to a JSON string
    local updated_json = cjson.encode(updated_data)

    -- Update the key with the new JSON value
    redis.call('SET', key, updated_json)
    return 1
else
    return 0
end
"""
