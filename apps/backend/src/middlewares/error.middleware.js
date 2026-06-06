import { ApiError } from "../utils/api-error.js";

const errorHandler = (err, req, res, next) => {
  let error = err;

  if (!(error instanceof ApiError)) {
    error = new ApiError(
      error.statusCode || 500,
      error.message || "Internal server error",
      error.errors || [],
      error.stack,
    );
  }

  return res.status(error.statusCode).json({
    statusCode: error.statusCode,
    data: error.data,
    message: error.message,
    success: error.success,
    errors: error.errors,
  });
};

export { errorHandler };
