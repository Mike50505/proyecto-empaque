export const isOrderComplete = row => row.published && Number(row.quantity) > 0 && Number(row.applied) >= Number(row.quantity);
