# Stage 1: Build the React application
FROM node:20-alpine as build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . ./
RUN npm run build

# Stage 2: Serve the application from a lightweight web server
FROM nginx:1.23-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Copy the nginx config to handle client-side routing
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
