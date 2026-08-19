import React from 'react';
import { Navigate } from 'react-router-dom';

export default function QuestionGenerator() {
  // Legacy standalone question generator has been integrated directly into the main Viva Creation Pipeline.
  return <Navigate to="/faculty/viva/create" replace />;
}
