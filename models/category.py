# ==================================================
# Category Model — Database Operations
# ==================================================

from models.db import execute_query


def get_all_categories():
    """Fetch all categories ordered by name."""
    return execute_query(
        "SELECT * FROM categories ORDER BY name",
        fetchall=True
    )


def get_category_by_id(category_id):
    """Fetch a single category by ID."""
    return execute_query(
        "SELECT * FROM categories WHERE id = %s",
        (category_id,),
        fetchone=True
    )


def create_category(name, description=None):
    """Create a new category. Returns the new category ID."""
    return execute_query(
        "INSERT INTO categories (name, description) VALUES (%s, %s)",
        (name, description),
        commit=True
    )


def update_category(category_id, name, description=None):
    """Update an existing category."""
    return execute_query(
        "UPDATE categories SET name = %s, description = %s WHERE id = %s",
        (name, description, category_id),
        commit=True
    )


def delete_category(category_id):
    """
    Delete a category.
    Will fail if products still reference it (ON DELETE RESTRICT).
    """
    return execute_query(
        "DELETE FROM categories WHERE id = %s",
        (category_id,),
        commit=True
    )


def category_name_exists(name, exclude_id=None):
    """Check if a category name is already taken."""
    if exclude_id:
        result = execute_query(
            "SELECT COUNT(*) AS count FROM categories WHERE name = %s AND id != %s",
            (name, exclude_id),
            fetchone=True
        )
    else:
        result = execute_query(
            "SELECT COUNT(*) AS count FROM categories WHERE name = %s",
            (name,),
            fetchone=True
        )
    return result['count'] > 0


def get_categories_with_product_count():
    """Fetch all categories with the count of active products in each."""
    return execute_query(
        """SELECT c.id, c.name, c.description, c.created_at,
                  COUNT(p.id) AS product_count
           FROM categories c
           LEFT JOIN products p ON c.id = p.category_id AND p.is_active = TRUE
           GROUP BY c.id, c.name, c.description, c.created_at
           ORDER BY c.name""",
        fetchall=True
    )
