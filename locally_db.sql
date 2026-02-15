CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS saved_businesses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    UNIQUE (user_id, business_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    UNIQUE (user_id, business_id)
);

-- Sample data (safe to re-run; businesses are inserted by unique name)
INSERT INTO users (username, email, password_hash) VALUES
    ('ava', 'ava@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('ben', 'ben@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('chloe', 'chloe@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('diego', 'diego@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('elena', 'elena@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('finn', 'finn@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('gia', 'gia@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('henry', 'henry@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('iris', 'iris@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('jules', 'jules@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('kiran', 'kiran@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d'),
    ('lana', 'lana@example.com', 'scrypt:32768:8:1$XaAwTEC3WJcVrtkA$05670c6891d74ac8f7f1405f10f05fa9cb4b0b14b436cd871d84c2d3d77a23e613e1d85540b6ddc8f613a0253869ae3c3331293c255d29dbd3e9799e16e0c85d')
ON CONFLICT DO NOTHING;

WITH sample_businesses (owner_id, name, category, description, location, verified) AS (
    VALUES
        (NULL::integer, 'Harbor & Hearth', 'Restaurant', 'Coastal bistro with seasonal plates and a warm, rustic vibe.', 'Seattle, WA', TRUE),
        (NULL::integer, 'Sunset Noodle Co.', 'Restaurant', 'Hand-pulled noodles, ramen and pho, open late.', 'Portland, OR', TRUE),
        (NULL::integer, 'Cedarstone Grill', 'Restaurant', 'Wood-fired grill featuring steaks, seafood, and smoked sides.', 'Denver, CO', FALSE),

        (NULL::integer, 'Thread & Timber', 'Clothing', 'Outdoor apparel and everyday layers made with sustainable fabrics.', 'Boise, ID', TRUE),
        (NULL::integer, 'Lumen Loft Boutique', 'Clothing', 'Modern womenswear, accessories, and seasonal capsule drops.', 'Austin, TX', TRUE),
        (NULL::integer, 'Northline Vintage', 'Clothing', 'Curated vintage finds from the 70s-90s with in-house tailoring.', 'Minneapolis, MN', FALSE),

        (NULL::integer, 'Skyline IT Solutions', 'Tech', 'Managed IT services, network setup, and security for small teams.', 'Chicago, IL', TRUE),
        (NULL::integer, 'PulseByte Labs', 'Tech', 'Custom web and mobile apps with rapid prototyping and UX design.', 'San Jose, CA', TRUE),
        (NULL::integer, 'GreenCloud Systems', 'Tech', 'Cloud migration, DevOps automation, and cost optimization.', 'Raleigh, NC', FALSE),

        (NULL::integer, 'Maple Street Auto', 'Automotive', 'Friendly neighborhood shop for maintenance, brakes, and diagnostics.', 'Columbus, OH', TRUE),
        (NULL::integer, 'Blue Ridge Detailing', 'Automotive', 'Premium detailing with ceramic coatings and interior restoration.', 'Asheville, NC', TRUE),
        (NULL::integer, 'Riverside Tire & Brake', 'Automotive', 'Tire sales, alignments, and brake service with quick turnaround.', 'Sacramento, CA', FALSE),

        (NULL::integer, 'Everwell Family Clinic', 'Health', 'Primary care focused on preventive medicine and same-week visits.', 'Omaha, NE', TRUE),
        (NULL::integer, 'Clearview Dental Studio', 'Health', 'Comprehensive dental care with cosmetic and restorative services.', 'Tampa, FL', TRUE),
        (NULL::integer, 'Harborview Physical Therapy', 'Health', 'Sports rehab and mobility-focused therapy programs.', 'Boston, MA', FALSE),

        (NULL::integer, 'BrightPipe Plumbing', 'Home Service (Repair)', 'Emergency plumbing, leak repair, and water heater installs.', 'Phoenix, AZ', TRUE),
        (NULL::integer, 'Summit Electric Co.', 'Home Service (Repair)', 'Residential electrical repairs, panel upgrades, and lighting.', 'Salt Lake City, UT', TRUE),
        (NULL::integer, 'Oak & Iron Handyman', 'Home Service (Repair)', 'Carpentry, drywall repair, and punch-list home fixes.', 'Pittsburgh, PA', FALSE),

        (NULL::integer, 'Beacon Bookshop', 'Other', 'Independent bookstore with author events and local zines.', 'Richmond, VA', TRUE),
        (NULL::integer, 'Starlight Pet Grooming', 'Other', 'Full-service grooming, nail trims, and spa packages for pets.', 'Tucson, AZ', TRUE),
        (NULL::integer, 'Crescent Event Rentals', 'Other', 'Event rentals for tents, chairs, lighting, and linens.', 'Nashville, TN', FALSE)
)
INSERT INTO businesses (owner_id, name, category, description, location, verified)
SELECT sb.owner_id, sb.name, sb.category, sb.description, sb.location, sb.verified
FROM sample_businesses sb
WHERE NOT EXISTS (
    SELECT 1 FROM businesses b WHERE b.name = sb.name
);

INSERT INTO ratings (user_id, business_id, rating)
SELECT u.id, b.id, r.rating
FROM (
    VALUES
        ('ava', 'Harbor & Hearth', 5),
        ('ben', 'Harbor & Hearth', 4),
        ('chloe', 'Harbor & Hearth', 5),

        ('diego', 'Sunset Noodle Co.', 3),
        ('elena', 'Sunset Noodle Co.', 5),
        ('finn', 'Sunset Noodle Co.', 2),

        ('gia', 'Cedarstone Grill', 2),
        ('henry', 'Cedarstone Grill', 4),
        ('iris', 'Cedarstone Grill', 3),

        ('jules', 'Thread & Timber', 5),
        ('kiran', 'Thread & Timber', 3),
        ('lana', 'Thread & Timber', 4),

        ('ava', 'Lumen Loft Boutique', 2),
        ('chloe', 'Lumen Loft Boutique', 3),
        ('elena', 'Lumen Loft Boutique', 4),

        ('ben', 'Northline Vintage', 5),
        ('finn', 'Northline Vintage', 2),
        ('iris', 'Northline Vintage', 3),

        ('diego', 'Skyline IT Solutions', 5),
        ('henry', 'Skyline IT Solutions', 3),
        ('jules', 'Skyline IT Solutions', 4),

        ('gia', 'PulseByte Labs', 2),
        ('kiran', 'PulseByte Labs', 5),
        ('lana', 'PulseByte Labs', 3),

        ('ava', 'GreenCloud Systems', 3),
        ('ben', 'GreenCloud Systems', 2),
        ('chloe', 'GreenCloud Systems', 4),

        ('elena', 'Maple Street Auto', 1),
        ('finn', 'Maple Street Auto', 3),
        ('iris', 'Maple Street Auto', 4),

        ('jules', 'Blue Ridge Detailing', 5),
        ('kiran', 'Blue Ridge Detailing', 4),
        ('lana', 'Blue Ridge Detailing', 2),

        ('diego', 'Riverside Tire & Brake', 2),
        ('henry', 'Riverside Tire & Brake', 3),
        ('gia', 'Riverside Tire & Brake', 4),

        ('ava', 'Everwell Family Clinic', 5),
        ('elena', 'Everwell Family Clinic', 4),
        ('finn', 'Everwell Family Clinic', 3),

        ('ben', 'Clearview Dental Studio', 2),
        ('chloe', 'Clearview Dental Studio', 5),
        ('jules', 'Clearview Dental Studio', 3),

        ('gia', 'Harborview Physical Therapy', 4),
        ('henry', 'Harborview Physical Therapy', 2),
        ('iris', 'Harborview Physical Therapy', 3),

        ('diego', 'BrightPipe Plumbing', 5),
        ('kiran', 'BrightPipe Plumbing', 3),
        ('lana', 'BrightPipe Plumbing', 1),

        ('elena', 'Summit Electric Co.', 4),
        ('finn', 'Summit Electric Co.', 2),
        ('ben', 'Summit Electric Co.', 5),

        ('chloe', 'Oak & Iron Handyman', 3),
        ('ava', 'Oak & Iron Handyman', 2),
        ('jules', 'Oak & Iron Handyman', 4),

        ('iris', 'Beacon Bookshop', 5),
        ('henry', 'Beacon Bookshop', 3),
        ('ben', 'Beacon Bookshop', 2),

        ('gia', 'Starlight Pet Grooming', 5),
        ('elena', 'Starlight Pet Grooming', 2),
        ('lana', 'Starlight Pet Grooming', 4),

        ('kiran', 'Crescent Event Rentals', 3),
        ('ava', 'Crescent Event Rentals', 2),
        ('diego', 'Crescent Event Rentals', 5)
) AS r(username, business_name, rating)
JOIN users u ON u.username = r.username
JOIN businesses b ON b.name = r.business_name
ON CONFLICT (user_id, business_id) DO UPDATE SET rating = EXCLUDED.rating;
