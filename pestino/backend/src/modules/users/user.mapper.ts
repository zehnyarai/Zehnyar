export interface UserRow {
  id: string;
  phone: string;
  full_name: string | null;
  province: string | null;
  city: string | null;
  role: 'farmer' | 'expert' | 'admin';
  is_active: boolean;
  last_login_at: Date | null;
  created_at: Date;
}

export interface PublicUser {
  id: string;
  phone: string;
  fullName: string | null;
  province: string | null;
  city: string | null;
  role: string;
  createdAt: string;
}

/** Maps a DB row to the API shape. Never leaks internal flags. */
export function toPublicUser(row: UserRow): PublicUser {
  return {
    id: row.id,
    phone: row.phone,
    fullName: row.full_name,
    province: row.province,
    city: row.city,
    role: row.role,
    createdAt: new Date(row.created_at).toISOString(),
  };
}
