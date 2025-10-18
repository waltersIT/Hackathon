import { StrictMode } from 'react'
//import { createRoot } from 'react-dom/client'
import ReactDom from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import './index.css'
import App from './App.tsx'
import Portfolios from './test-pages/portfolios.tsx';
import PortfoliosB from './test-pages/portfoliosB.tsx';

const router = createBrowserRouter([
  {
  path: '/',
  element: <App />,
},
  {
  path: '/portfolios/351',
  element: <Portfolios />,
},
{
  path: '/portfolios/297',
  element: <PortfoliosB />,
},
])
ReactDom.createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)