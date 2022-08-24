FROM node:alpine AS builder
ENV NODE_ENV production
# Add a work directory
WORKDIR /app
# Cache and Install dependencies
COPY ./frontend-react/package.json .
COPY ./frontend-react/yarn.lock .

RUN yarn install --production
# Copy app files
COPY ./frontend-react .
# Build the app
RUN yarn build

# Bundle static assets with nginx
FROM nginx:alpine as production
ENV NODE_ENV production
# Copy built assets from builder
COPY --from=builder /app/build /usr/share/nginx/html
# Add your nginx.conf
COPY ./frontend-react/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80
# Start nginx
CMD ["nginx", "-g", "daemon off;"]