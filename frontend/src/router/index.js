import { createRouter, createWebHistory } from "vue-router";
import HomeView from "@/components/HomeView.vue";
import UserLogin from "@/components/UserLogin.vue";
import AdminLogin from "@/components/AdminLogin.vue";
import SignUp from "@/components/SignUp.vue";
import UserDashboard from "@/components/UserDashboard.vue";
import AdminDashboard from "@/components/AdminDashboard.vue";
import EditProfile from "@/components/EditProfile.vue";
import UserManagement from '@/components/UserManagement.vue';
import QuizAdmin  from "@/components/QuizAdmin.vue";
import QuestionCreate from "@/components/QuestionCreate.vue";
import TakeQuiz from "@/components/TakeQuiz.vue";
import ReportDashboard from "@/components/ReportDashboard.vue";


const routes = [
  { path: "/", name: "home", component: HomeView, },
  { path: "/user-login", name: "userLogin", component: UserLogin, meta: { defaultnavbar: true } },
  { path: "/admin-login", name: "adminLogin", component: AdminLogin, meta: { defaultnavbar: true } },
  { path: "/signup", name: "signUp", component: SignUp, meta: { defaultnavbar: true } },
  { path: "/user-dashboard", name: "userDashboard", component: UserDashboard, meta: { defaultnavbar: true, requiresAuth: true, role: "user" } },
  { path: "/admin-dashboard", name: "adminDashboard", component: AdminDashboard, meta: { defaultnavbar: true, requiresAuth: true, role: "admin" }, props: (route) => ({ searchQuery: route.query.q || '' }) },
  { path: "/edit-profile", name: "editProfile", component: EditProfile, meta: { requiresAuth: true } },
  { path: "/admin/question-create/:quizId", name: "question-create", component: QuestionCreate,props: route => ({ quizId: Number(route.params.quizId),quizTitle: route.query.quizTitle || "Unknown Quiz" }), meta: { requiresAuth: true } },
  { path: "/:pathMatch(.*)*", redirect: "/user-login" },
  { path: '/admin/manage-users', name: 'UserManagement', component: UserManagement, meta: {defaultnavbar: true, requiresAuth: true, role: 'admin' } },
  { path: '/admin/manage-quizzes', name: 'QuizAdmin', component: QuizAdmin, meta: {defaultnavbar: true, requiresAuth: true, role: 'admin' } },
  { path: '/quiz-attempt/:quizId',name: 'TakeQuiz', component: TakeQuiz },
  { path: '/reports', name: 'ReportDashboard', component: ReportDashboard, meta: {defaultnavbar: true, requiresAuth: true } }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
    const user = localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")) : null;

    if (user && (to.path === "/user-login" || to.path === "/signup")) {
      next("/user-dashboard");
      return;
    }

    if (user && to.path === "/admin-login") {
      next("/admin-dashboard");
      return;
    }

    if (to.meta.requiresAuth) {
      if (!user) {
        next(to.meta.role === "admin" ? "/admin-login" : "/user-login");
        return;
      }

      if (to.meta.role && user.role !== to.meta.role) {
        next(user.role === "admin" ? "/admin-dashboard" : "/user-dashboard");
        return;
      }
    }

    next();
});

export default router;
